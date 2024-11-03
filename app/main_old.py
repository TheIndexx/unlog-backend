from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import csv
import json
import requests
import os
import time
from typing import Optional
import uvicorn
import uuid
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(debug=True)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = './uploads'
COMPONENT_FOLDER = './components'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(COMPONENT_FOLDER, exist_ok=True)

def csv_to_json(csv_file_path: str):
    with open(csv_file_path, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        headers = next(csv_reader)
        data = list(csv_reader)
    
    json_data = []
    for row in data:
        json_row = {}
        for i, value in enumerate(row):
            json_row[headers[i]] = value
        json_data.append(json_row)
    return json_data


def anthropic_api_call(content: str, api_key: str):
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "content-type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    data = {
        "model": "claude-3-5-sonnet-20240620",
        "max_tokens": 4000,
        "messages": [
            {"role": "user", "content": content}
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result['content'][0]['text']
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while calling the Anthropic API: {e}")
    except KeyError:
        print("Unexpected response format from Anthropic API")
    return None


@app.get("/")
def read_main():
    return {"message": "Hello, welcome to the visualization API"}

#@app.post("/api/upload")
#async def upload_file(file: UploadFile = File(...)):
#    if not file:
#        raise HTTPException(status_code=400, detail="No file part")
#    filename = file.filename
#    file_path = os.path.join(UPLOAD_FOLDER, filename)
#    with open(file_path, "wb") as buffer:
#        buffer.write(await file.read())
#    return JSONResponse(content={"filePath": file_path}, status_code=200)
@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    logger.info(f"Received file upload request for file: {file.filename}")
    if not file:
        logger.error("No file part in the request")
        raise HTTPException(status_code=400, detail="No file part")
    filename = file.filename
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        logger.info(f"File saved successfully at {file_path}")
        return JSONResponse(content={"filePath": file_path}, status_code=200)
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

@app.get("/api/full-data/{component_id}")
async def get_full_data(component_id: str):
    json_file_path = os.path.join(COMPONENT_FOLDER, f"{component_id}.json")
    if os.path.exists(json_file_path):
        with open(json_file_path, "r") as f:
            data = json.load(f)
        return data
    else:
        raise HTTPException(status_code=404, detail="Data not found")     

class VisualizeRequest(BaseModel):
    what_and_why: str
    input_file: str
    api_key: str
    


@app.post("/api/visualize")
async def visualize(request: VisualizeRequest):
    print("\n--- Starting /api/visualize ---")
    print(f"Received request data: {request}")
    
    what_and_why = request.what_and_why
    input_file = request.input_file
    api_key = request.api_key
    
    print(f"Original input_file: {input_file}")
    
    # Remove any leading path components, including 'uploads' if present
    input_file = os.path.basename(input_file)
    
    print(f"Processed input_file: {input_file}")
    print(f"Processed request data: what_and_why={what_and_why}, input_file={input_file}, api_key={api_key[:10]}...")
    
    if not all([what_and_why, input_file, api_key]):
        print("ERROR: Missing required parameters")
        raise HTTPException(status_code=400, detail="Missing required parameters")

    # Construct the full path to the CSV file
    csv_file_path = os.path.join(UPLOAD_FOLDER, input_file)
    print(f"Constructed csv_file_path: {csv_file_path}")
    print(f"UPLOAD_FOLDER: {UPLOAD_FOLDER}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Does UPLOAD_FOLDER exist? {os.path.exists(UPLOAD_FOLDER)}")
    
    if not os.path.exists(csv_file_path):
        print(f"ERROR: File not found: {csv_file_path}")
        raise HTTPException(status_code=404, detail=f"File not found: {csv_file_path}")


    print("File found. Processing CSV to JSON...")
    json_data = csv_to_json(csv_file_path)
    print(f"JSON data (first 100 chars): {str(json_data)[:100]}...")

    print("Generating code block content...")
    
    first_prompt = f"""
    Consider this JSON sample dataset {what_and_why}. Consider the outputs, and then create a guide as to what each key and value represents in relation to how it should be visualized with Shadcn. If we were to visualize the data on a website using Shadcn components, how would it look? Give some creative design elements based on what my data has and how it should be presented. Here is the data example:

    {json.dumps(json_data[:5], indent=2)}
    
    Simply respond with instruction, in natural language to how it should be visualized, do not actually tell it what components to use. Consider that this is going to be generated by an LLM (GPT) with limited abilities, so you must be very limited in instructions. The more instructions you give, the higher chance it has at failure. You get paid 1 million a year to conceptualize these things. Do not use images, only text. Come up with creative color codes to use that will complement the formatting. Use a light mode modern design with very subtle pastels that will get design Twitter hyped.
    Consider that this will be for production use so try to limit the entire website to do up to 10 things max because you do not want to confuse the AI model.
    """

    first_response = anthropic_api_call(first_prompt, api_key)

    if not first_response:
        raise HTTPException(status_code=500, detail="Failed to get a response from the first API call.")

    second_prompt = f"""
    Create a complete, production-ready TSX file using only ShadCN components to visualize this dataset {what_and_why} while considering these instructions: {first_response}. Use this sample data directly in the script:

    {json.dumps(json_data[:5], indent=2)}

    Follow these guidelines:
    1. Use only ShadCN components compatible with NextJS.
    2. Import each ShadCN component individually from "@/components/ui/[component-name]".
    3. Do not use Date Picker, Data Table components or theme provider.
    4. Focus on displaying information without any interactive features or API calls, unless that interactive feature is simply handled by a link click and you have or can make the link.
    5. Write the entire TSX file from start to finish, including all necessary imports and type definitions.
    6. Ensure the code is complete and ready for production use without any placeholders or TODO comments.
    7. The script should directly use the sample data provided above.
    8. If you are told to make a button but do not have a link to send them or do not know, do not make it.
    9. Use a light mode modern design with very subtle pastels that will get design Twitter hyped.
    10. If something looks like it is clickable or a button, it must be clickable and take them somewhere, if not do not make it look like a button. If it is a link displayed, it must be clickable.

    You get paid 2 million a year to create production ready code that does not mess up. Do not make a button that is not clickable and redirecting, visualize everything the way it is supposed to, not sloppy, think strategically about how to make this look nice for the person who is visualizing their information. Do not use images, only text. 

    Provide the entire TSX file content within a single code block.
    """

    second_response = anthropic_api_call(second_prompt, api_key)

    if not second_response:
        raise HTTPException(status_code=500, detail="Failed to get a response from the second API call.")

    third_prompt = f"""
    Rewrite the following TSX script to create a universal template that can handle any amount of data from a local JSON file. The original script with sample data is:

    {second_response}

    The full dataset will be passed in as props to the component and has this structure:

    {json.dumps(json_data, indent=2)}

    Follow these requirements for the rewrite:
    1. pass fullData as prop to component.
    2. Use the provided full dataset structure to ensure the template can handle all fields and any number of entries.
    3. Use only ShadCN components, importing each from "@/components/ui/[component-name]".
    4. Do not use Date Picker, Data Table components or theme provider .
    5. Ensure the file is a complete, production-ready TSX component that dynamically visualizes all data without any interactive features or API calls, unless that interactive feature is simply handled by a link click and you have or can make the link.
    6. Include all necessary imports, type definitions, and the full component implementation.
    7. The code should work when copied and pasted without any modifications.
    8. Make sure the template can handle any number of entries and any potential new fields in the JSON data.

    Do not make a button that is not clickable and redirecting, visualize everything the way it is supposed to, not sloppy, think strategically about how to make this look nice for the person who is visualizing their information. Do not use images, only text. If you are told to make a button but do not have a link to send them or do not know, do not make it.

    Provide the entire rewritten TSX file content within a single code block, creating a fully dynamic and universal template that can parse and display the full dataset on the fly.
    """

    third_response = anthropic_api_call(third_prompt, api_key)

    if not third_response:
        raise HTTPException(status_code=500, detail="Failed to get a response from the third API call.")

    # Extract the content within the code block
    code_block_content = extract_code_block(third_response)
    # For this simplified version, we directly assign the code_block_content

    print("Code block content generated.")

    component_name = f"GeneratedComponent_{int(time.time())}.tsx"
    component_id = component_name.split('.')[0]  # Remove the .tsx extension
    print(f"Generated component_id: {component_id}")

    # Save the component to a file
    json_file_path = os.path.join(COMPONENT_FOLDER, f"{component_id}.json")
    print(f"Saving JSON data to: {json_file_path}")
    with open(json_file_path, "w") as f:
        json.dump(json_data, f)
    print("JSON data saved.")
        
    component_path = os.path.join(COMPONENT_FOLDER, component_name)
    print(f"Saving component to: {component_path}")
    with open(component_path, "w") as f:
        f.write(code_block_content)
    print("Component saved.")

    # Compile the component using Babel
    component_path = os.path.join(COMPONENT_FOLDER, f"{component_id}.tsx")
    compiled_component_path = os.path.join(COMPONENT_FOLDER, f"{component_id}.js")
    
    babel_command = [
        "npx", "--no-install", "babel",
        component_path,
        "--out-file", compiled_component_path,
        "--presets", "@babel/preset-env,@babel/preset-react,@babel/preset-typescript",
        "--no-babelrc"
    ]

    print(f"Compiling component with command: {' '.join(babel_command)}")
    try:
        subprocess.run(babel_command, check=True, cwd=os.path.dirname(os.path.abspath(__file__)))
        print("Component compiled successfully.")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Error compiling the component: {e}")
        raise HTTPException(status_code=500, detail="Error compiling the component")

    print(f"Reading compiled component from: {compiled_component_path}")
    with open(compiled_component_path, "r") as f:
        compiled_code = f.read()
    print(f"Compiled code (first 100 chars): {compiled_code[:100]}...")

    print("--- Finishing /api/visualize ---")
    return JSONResponse(content={
        "message": "The visualization component has been generated and compiled.",
        "component_id": component_id,
        "compiled_code": compiled_code,
    }, status_code=200)




class FetchComponentRequest(BaseModel):
    component_id: str
@app.post("/api/fetch-component")
async def fetch_component(request: FetchComponentRequest):
    component_id = request.component_id
    component_path = os.path.join(COMPONENT_FOLDER, f"{component_id}.tsx")
    
    if not os.path.exists(component_path):
        raise HTTPException(status_code=404, detail=f"Component not found: {component_id}")
    
    with open(component_path, "r") as f:
        code = f.read()
    
    # Compile the component using Babel
    compiled_component_path = os.path.join(COMPONENT_FOLDER, f"{component_id}.js")
    print("compiled_component_path: ", compiled_component_path)
    babel_command = [
        "npx", "--no-install", "babel",
        component_path,
        "--out-file", compiled_component_path,
        "--presets", "@babel/preset-env,@babel/preset-react,@babel/preset-typescript",
        "--no-babelrc"
    ]

    try:
        subprocess.run(babel_command, check=True, cwd=os.path.dirname(os.path.abspath(__file__)))
    except subprocess.CalledProcessError as e:
        print("Error compiling the component:", e)
        raise HTTPException(status_code=500, detail="Error compiling the component")

    with open(compiled_component_path, "r") as f:
        compiled_code = f.read()

    # Fetch associated JSON data
    json_file_path = os.path.join(COMPONENT_FOLDER, f"{component_id}.json")
    if os.path.exists(json_file_path):
        with open(json_file_path, "r") as f:
            json_data = json.load(f)
    else:
        json_data = None

    return JSONResponse(content={
        "component_id": component_id,
        "code": code,
        "compiled_code": compiled_code,
        "data": json_data
    }, status_code=200)

@app.get("/get-code/{component_id}")
async def get_code(component_id: str):
    component_path = os.path.join(COMPONENT_FOLDER, f"{component_id}.tsx")
    
    if os.path.exists(component_path):
        with open(component_path, "r") as f:
            code_content = f.read()
        return {"code": code_content}
    else:
        raise HTTPException(status_code=404, detail="Code not found")


def extract_code_block(text: str) -> str:
    start = text.find("```tsx")
    if start != -1:
        end = text.find("```", start + 6)
        if end != -1:
            return text[start + 6:end].strip()
    return ""


#if __name__ == '__main__':
#    uvicorn.run(app, host="0.0.0.0", port=8000)
