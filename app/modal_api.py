import os
import json
import modal
from modal import Image, Secret, App, Dict
from functions import get_current_user, reduce_user_credits, anthropic_api_call, upload_to_s3, read_from_s3, get_user_ui_names, extract_code_block, fetch_component_status, set_component_status, anthropic_api_call_data_cleaner, update_component_privacy
from prompt_new import o1_line_by_line_prompt, second_o1_prompt, claude_prompt
from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Union
from enum import Enum
from preprocessing import csv_to_json, clean_key, to_camel_case, clean_value, standardize_data_types, handle_missing_values, normalize_strings, handle_currency, json_to_csv, sample_df_with_char_limit
import pandas as pd
import random
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Header
import io
from openai import AsyncOpenAI
import csv
import asyncio
from datetime import datetime

load_dotenv('.env.local')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ID = os.getenv('AWS_SECRET_ID')
import subprocess

# Define image with necessary dependencies
image = (
    Image.debian_slim(python_version="3.11.9")
    .pip_install("anthropic", "python-dotenv", "boto3", "chardet", "uvicorn", "clerk-sdk-python", "awscli", "pandas", "tenacity", "openpyxl", "openai", "tabulate", "pydantic")
    .apt_install("nodejs", "npm")
    .run_commands(
        "mkdir -p /app",
        "cd /app && npm init -y",
        "cd /app && npm install @babel/core @babel/cli @babel/preset-env @babel/preset-react @babel/preset-typescript"
    )
    .copy_local_file(".babelrc", "/app/.babelrc")
)

S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

# Define main Modal app
app = modal.App("code-generation-app-prod", image=image)

# Define Dict for job statuses
job_statuses = Dict.from_name("job-statuses", create_if_missing=True)

# Input model for generate_code_api
class InputGenerateCode(BaseModel):
    user_id: str
    what_and_why: str
    s3_file_path: str 
    component_id: str
    
def compile_component(temp_tsx_path, temp_js_path):
    babel_bin = "/app/node_modules/.bin/babel"
    babel_command = [
        babel_bin,
        temp_tsx_path,
        "--out-file", temp_js_path,
        "--presets", "@babel/preset-env,@babel/preset-react,@babel/preset-typescript"
    ]
    
    print("Checking npm and Babel installation:")
    subprocess.run(["npm", "--version"], check=True)
    subprocess.run([babel_bin, "--version"], check=True)
    subprocess.run(["ls", "-l", "/app/node_modules/@babel"], check=True)
    
    print(f"Compiling component with command: {' '.join(babel_command)}")
    try:
        subprocess.run(babel_command, check=True, cwd="/app")
        print("Component compiled successfully.")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Error compiling the component: {e}")
        return None  # or handle this error as appropriate
    

async def openai_o1_api_call(user_message: str, openai_client) -> str:
    try:
        response = await openai_client.chat.completions.create(
            # model="o1-preview",
            # model="gpt-4o",
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"openai_o1_api_call(): Error calling OpenAI API: {str(e)}")
        with open('./prompt_0.txt', 'w') as f:
            f.write(user_message)
            quit()
        return 'Error occurred'
    

async def openai_gpt4mini_schema_call(user_message: str, schema, openai_client) -> str:
    try:
        completion = await openai_client.beta.chat.completions.parse(
            # model="gpt-4o",
            model="got-4o-mini",
            messages=[
                {"role": "user", "content": user_message}
            ],
            response_format=schema,

        )
        return completion.choices[0].message.parsed
    except Exception as e:
        print(f"openai_gpt4mini_schema_call(): Error calling OpenAI API: {str(e)}")
        with open('./prompt.txt', 'w') as f:
            f.write(user_message)
            quit()
        return 'Error occurred'



def execute_python_with_timeout(code: str, timeout: int = 600):
    load_dotenv()
    try:
        exec(code, globals())
    except Exception as e:
        print(f"Python execution failed with error {e}")


def pydantic_model_to_string(model: BaseModel) -> str:
    field_info_list = []
    
    for field_name, field_info in model.__fields__.items():
        field_info_list.append(
            f"Field: {field_name}\n"
            f"Type: {field_info.type_}\n"
            f"Description: {field_info.field_info.description}\n"
        )
    
    # Join all field information into a single string
    return "\n".join(field_info_list)


async def enhance_csv_row(row, prompt, data_sample_str, schema, openai_client):
    full_prompt = f"""
    You are part of a billion-dollar human + computer system that aims to enhance datasets so eventually data analysts can answer business professional's queries on these datasets. Your task is the first part of the system, which is to operate on ONE SINGLE ROW at a time and enhance it as best as possible, according to the specific instructions you have been given and adhering to that format.

    Here is a sample of the current dataset you are operating on: "{data_sample_str}"
    Here are the instructions for how to operate on the row of data that will be given below:
    "{prompt}"

    REMEMBER, YOU ARE ONLY OPERATING ON ONE ROW AT A TIME, AND CURRENTLY YOU ARE OPERATING ON THE ROW THAT WILL BE PROVIDED BELOW. ENHANCE THE ROW AS REQUESTED. Also know that on some rows many of the columns may not be appliable and in this case, make those fields null or empty or so on, rather than forcing unreliable data. This is very important to adhere to.

    HERE IS THE SINGLE ROW OF DATA YOU ARE OPERATING ON AND MUST ENHANCE: {row}
    """
    filled_out_schema = await openai_gpt4mini_schema_call(full_prompt, schema, openai_client)
    new_fields = filled_out_schema.dict()
    row.update(new_fields)
    return row


def get_sample_from_csv(csv_file, NUM_ROWS_TO_SAMPLE = 100):
    df = pd.read_csv(csv_file)
    sample_df = df.sample(n=NUM_ROWS_TO_SAMPLE, random_state=42)
    data_sample_string = sample_df.to_string(index=False)
    return data_sample_string


async def generate_code_local(user_id, what_and_why, s3_file_path, component_id):
    AWS_SECRET_ID = os.environ['AWS_SECRET_ID']
    AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
    ANTHROPIC_API_KEY = os.environ['ANTHROPIC_API_KEY']
    CLERK_SECRET_KEY = os.environ['CLERK_SECRET_KEY']
    OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

    openai_client = AsyncOpenAI(
        # This is the default and can be omitted
        api_key=OPENAI_API_KEY,
    )
    
    # Extract bucket name, folder, and key from s3_file_path
    _, _, bucket, s3_key = s3_file_path.split('/', 3)
    s3_key_folder, s3_key = os.path.split(s3_key)
    
    json_data = csv_to_json(bucket, s3_key_folder, s3_key, AWS_ACCESS_KEY_ID, AWS_SECRET_ID)
    csv_data = json_to_csv(json_data)
    csv_data_io = io.StringIO(csv_data)
    data_sample_string = get_sample_from_csv(csv_data_io)

    print(f"yoyo here's csv data: {data_sample_string}")

    new_columns_description = ""
    SELF_AWARENESS = 1
    
    for iteration in range(1, SELF_AWARENESS + 1):
        formatted_first_prompt = o1_line_by_line_prompt.format(
            WHAT_AND_WHY=what_and_why,
            CSV_DATA=data_sample_string,
            ITERATION=iteration,
            ITERATIONS=SELF_AWARENESS,
        )
        response = await openai_o1_api_call(formatted_first_prompt, openai_client)
        if not response:
            raise HTTPException(status_code=500, detail="Failed to get a response from the first API call.")
        
        print(response)    
        per_line_prompt, pydantic_model_code = extract_code_block(response, "prompt"), extract_code_block(response, "python")
        namespace = {}
        exec(pydantic_model_code, globals(), namespace)
        RowEnrichment = namespace['RowEnrichment']
        print('LOADED PYDANTIC MODEL: ', RowEnrichment.__fields__.keys())

        rows = []
        # Open the CSV file and read it using DictReader
        reader = csv.DictReader(csv_data_io)
        for row in reader:
            rows.append(row)

        tasks = [
            enhance_csv_row(row, per_line_prompt, data_sample_string, RowEnrichment, openai_client) for row in rows
        ]
        enhanced_rows = await asyncio.gather(*tasks)

        fieldnames = reader.fieldnames + list(RowEnrichment.__fields__.keys())        
        enhanced_csv_data_io = io.StringIO()
        writer = csv.DictWriter(enhanced_csv_data_io, fieldnames=fieldnames)
        writer.writeheader()  # Write the header row
        writer.writerows(enhanced_rows)  # Write the modified rows

        new_columns_description += pydantic_model_to_string(RowEnrichment)

        # Get the output CSV data as a string
        enhanced_csv_data = enhanced_csv_data_io.getvalue()
        updated_sample_string = get_sample_from_csv(io.StringIO(enhanced_csv_data))

        # print('CURRENT DATA SAMPLE', updated_sample_string)
        print('CURRENT COLUMNS:', fieldnames)

        data_sample_string = updated_sample_string
        csv_data_io = io.StringIO(enhanced_csv_data)
    
    formatted_second_prompt = second_o1_prompt.format(
        WHAT_AND_WHY=what_and_why,
        CSV_DATA=data_sample_string,
        NEW_COLUMNS=new_columns_description
    )
    
    second_response = await openai_o1_api_call(formatted_second_prompt, openai_client)
    print("second_response: ", second_response)
    
    if not second_response:
        raise HTTPException(status_code=500, detail="Failed to get a response from the second API call.")
    
    python_code = extract_code_block(second_response, 'python') or extract_code_block(second_response, 'py')
    python_file_path = os.path.join("/tmp", "analysis.py")

    python_code = python_code.replace('if __name__ == "__main__":', 'if 1:')
    python_code = python_code.replace("if __name__ == '__main__':", 'if 1:')

    print(f"python code: {python_code}")
    with open(python_file_path, "w") as f:
        f.write(python_code)
    
    original_cwd = os.getcwd()
    os.chdir('/tmp')

    csv_path = os.path.join('/tmp', 'input.csv')
    with open(csv_path, "w") as f:
        f.write(enhanced_csv_data)

    # Execute the Python code
    execute_python_with_timeout(python_code)

    try:
        with open("./report.md") as f:
            result = f.read()
        print(f"Python code executed. Output MD: {result}...")

    except FileNotFoundError:
        print('report.md not found, python execution failed')
        result = "#Error"
        try: 
            with open("./script.log") as f:
                logs = f.read()
                print(f"PYTHON LOGS: {logs}")
        except:
            print('logs not found')
            pass

    # Change back to the original working directory
    os.chdir(original_cwd)

    claude_prompt_formatted = claude_prompt.format(
        what_and_why=what_and_why,
        result=result,
    ) 

    claude_response = anthropic_api_call(claude_prompt_formatted, ANTHROPIC_API_KEY)

    code_block_content = extract_code_block(claude_response, 'jsx')
    
    temp_tsx_path = os.path.join("/tmp", f"{component_id}.tsx")
    temp_js_path = os.path.join("/tmp", f"{component_id}.js")
    temp_json_path = os.path.join("/tmp", f"{component_id}.json")
    
    # Write the TypeScript code to a file
    print("code_block_content; ", code_block_content)
    with open(temp_tsx_path, "w") as f:
        f.write(code_block_content)
    
    if os.path.exists(temp_tsx_path):
       print(f"File created successfully at {temp_tsx_path}")
       with open(temp_tsx_path, "r") as f:
           print("File content:", f.read())
    else:
       print(f"Failed to create file at {temp_tsx_path}")
    

    # Write the JSON data to a file
    with open(temp_json_path, "w") as f:
        json.dump(json_data, f)
    
    compile_component(temp_tsx_path, temp_js_path)

    try:
        with open(temp_js_path, "r") as f:
            compiled_code = f.read()
        print(f"Compiled code (first 100 chars): {compiled_code[:100]}...")
    except FileNotFoundError:
        print(f"ERROR: Compiled JavaScript file not found at {temp_js_path}")
        return None  # or handle this error as appropriate

    s3_key_folder = os.path.join(str(user_id), component_id)
    upload_results = [
        upload_to_s3(temp_tsx_path, S3_BUCKET_NAME, s3_key_folder, f"{component_id}.tsx", AWS_ACCESS_KEY_ID, AWS_SECRET_ID),
        upload_to_s3(temp_js_path, S3_BUCKET_NAME, s3_key_folder, f"{component_id}.js", AWS_ACCESS_KEY_ID, AWS_SECRET_ID),
        upload_to_s3(temp_json_path, S3_BUCKET_NAME, s3_key_folder, f"{component_id}.json", AWS_ACCESS_KEY_ID, AWS_SECRET_ID)
    ]

    s3_upload_success = all(result is not None for result in upload_results)

    if s3_upload_success:
        print("All files uploaded successfully to S3.")
        print("S3 paths:", upload_results)
        
        await set_component_status(component_id, "completed")
        
        await update_component_privacy(user_id, component_id, True, clerk_secret_key=CLERK_SECRET_KEY)
    else:
        failed_uploads = [f"{ext}" for ext, result in zip(["tsx", "js", "json"], upload_results) if result is None]
        print(f"Failed to upload the following files: {', '.join(failed_uploads)}")
        await set_component_status(component_id, "failed")
    
    # Clean up temporary files
    # for file_path in [temp_tsx_path, temp_js_path, temp_json_path]:
    #     try:
    #         os.remove(file_path)
    #     except FileNotFoundError:
    #         print(f"Warning: Could not delete {file_path} as it was not found.")

    return code_block_content

@app.function(image=image, timeout=60 * 15)
async def generate_code(user_id, what_and_why, s3_file_path, component_id):
    AWS_SECRET_ID = os.environ['AWS_SECRET_ID']
    AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
    ANTHROPIC_API_KEY = os.environ['ANTHROPIC_API_KEY']
    CLERK_SECRET_KEY = os.environ['CLERK_SECRET_KEY']
    OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

    openai_client = AsyncOpenAI(
        # This is the default and can be omitted
        api_key=OPENAI_API_KEY,
    )
    
    # Extract bucket name, folder, and key from s3_file_path
    _, _, bucket, s3_key = s3_file_path.split('/', 3)
    s3_key_folder, s3_key = os.path.split(s3_key)
    
    json_data = csv_to_json(bucket, s3_key_folder, s3_key, AWS_ACCESS_KEY_ID, AWS_SECRET_ID)
    csv_data = json_to_csv(json_data)
    csv_data_io = io.StringIO(csv_data)
    data_sample_string = get_sample_from_csv(csv_data_io)

    print(f"yoyo csv data: {data_sample_string}")

    new_columns_description = ""
    SELF_AWARENESS = 4
    
    for iteration in range(1, SELF_AWARENESS + 1):
        formatted_first_prompt = o1_line_by_line_prompt.format(
            WHAT_AND_WHY=what_and_why,
            CSV_DATA=data_sample_string,
            ITERATION=iteration,
            ITERATIONS=SELF_AWARENESS,
        )
        response = await openai_o1_api_call(formatted_first_prompt, openai_client)
        if not response:
            raise HTTPException(status_code=500, detail="Failed to get a response from the first API call.")
        
        print(response)    
        per_line_prompt, pydantic_model_code = extract_code_block(response, "prompt"), extract_code_block(response, "python")
        namespace = {}
        exec(pydantic_model_code, globals(), namespace)
        RowEnrichment = namespace['RowEnrichment']
        print('LOADED PYDANTIC MODEL: ', RowEnrichment.__fields__.keys())

        rows = []
        # Open the CSV file and read it using DictReader
        reader = csv.DictReader(csv_data_io)
        for row in reader:
            rows.append(row)

        tasks = [
            enhance_csv_row(row, per_line_prompt, data_sample_string, RowEnrichment, openai_client) for row in rows
        ]
        enhanced_rows = await asyncio.gather(*tasks)

        fieldnames = reader.fieldnames + list(RowEnrichment.__fields__.keys())        
        enhanced_csv_data_io = io.StringIO()
        writer = csv.DictWriter(enhanced_csv_data_io, fieldnames=fieldnames)
        writer.writeheader()  # Write the header row
        writer.writerows(enhanced_rows)  # Write the modified rows

        new_columns_description += pydantic_model_to_string(RowEnrichment)

        # Get the output CSV data as a string
        enhanced_csv_data = enhanced_csv_data_io.getvalue()
        updated_sample_string = get_sample_from_csv(io.StringIO(enhanced_csv_data))

        print('CURRENT DATA SAMPLE', updated_sample_string)

        data_sample_string = updated_sample_string
        csv_data_io = io.StringIO(enhanced_csv_data)
    
    formatted_second_prompt = second_o1_prompt.format(
        WHAT_AND_WHY=what_and_why,
        CSV_DATA=data_sample_string,
        NEW_COLUMNS=new_columns_description
    )
    
    second_response = await openai_o1_api_call(formatted_second_prompt, openai_client)
    print("second_response: ", second_response)
    
    if not second_response:
        raise HTTPException(status_code=500, detail="Failed to get a response from the second API call.")
    
    python_code = extract_code_block(second_response, 'python') or extract_code_block(second_response, 'py')
    python_file_path = os.path.join("/tmp", "analysis.py")

    python_code = python_code.replace('if __name__ == "__main__":', 'if 1:')
    python_code = python_code.replace("if __name__ == '__main__':", 'if 1:')

    print(f"python code: {python_code}")
    with open(python_file_path, "w") as f:
        f.write(python_code)
    
    original_cwd = os.getcwd()
    os.chdir('/tmp')

    csv_path = os.path.join('/tmp', 'input.csv')
    with open(csv_path, "w") as f:
        f.write(enhanced_csv_data)

    # Execute the Python code
    execute_python_with_timeout(python_code)

    try:
        with open("./report.md") as f:
            result = f.read()
        print(f"Python code executed. Output MD: {result}...")

    except FileNotFoundError:
        print('report.md not found, python execution failed')
        result = "#Error"
        try: 
            with open("./script.log") as f:
                logs = f.read()
                print(f"PYTHON LOGS: {logs}")
        except:
            print('logs not found')
            pass

    # Change back to the original working directory
    os.chdir(original_cwd)

    claude_prompt_formatted = claude_prompt.format(
        what_and_why=what_and_why,
        result=result,
    ) 

    claude_response = anthropic_api_call(claude_prompt_formatted, ANTHROPIC_API_KEY)

    code_block_content = extract_code_block(claude_response, 'jsx')
    
    temp_tsx_path = os.path.join("/tmp", f"{component_id}.tsx")
    temp_js_path = os.path.join("/tmp", f"{component_id}.js")
    temp_json_path = os.path.join("/tmp", f"{component_id}.json")
    
    
    # Write the TypeScript code to a file
    print("code_block_content; ", code_block_content)
    with open(temp_tsx_path, "w") as f:
        f.write(code_block_content)
    
    if os.path.exists(temp_tsx_path):
       print(f"File created successfully at {temp_tsx_path}")
       with open(temp_tsx_path, "r") as f:
           print("File content:", f.read())
    else:
       print(f"Failed to create file at {temp_tsx_path}")
    


    # Write the JSON data to a file
    with open(temp_json_path, "w") as f:
        json.dump(json_data, f)
    
    compile_component(temp_tsx_path, temp_js_path)

    try:
        with open(temp_js_path, "r") as f:
            compiled_code = f.read()
        print(f"Compiled code (first 100 chars): {compiled_code[:100]}...")
    except FileNotFoundError:
        print(f"ERROR: Compiled JavaScript file not found at {temp_js_path}")
        return None  # or handle this error as appropriate

    s3_key_folder = os.path.join(str(user_id), component_id)
    upload_results = [
        upload_to_s3(temp_tsx_path, S3_BUCKET_NAME, s3_key_folder, f"{component_id}.tsx", AWS_ACCESS_KEY_ID, AWS_SECRET_ID),
        upload_to_s3(temp_js_path, S3_BUCKET_NAME, s3_key_folder, f"{component_id}.js", AWS_ACCESS_KEY_ID, AWS_SECRET_ID),
        upload_to_s3(temp_json_path, S3_BUCKET_NAME, s3_key_folder, f"{component_id}.json", AWS_ACCESS_KEY_ID, AWS_SECRET_ID)
    ]

    s3_upload_success = all(result is not None for result in upload_results)

    if s3_upload_success:
        print("All files uploaded successfully to S3.")
        print("S3 paths:", upload_results)
        
        await set_component_status(component_id, "completed")
        
        await update_component_privacy(user_id, component_id, True, clerk_secret_key=CLERK_SECRET_KEY)
    else:
        failed_uploads = [f"{ext}" for ext, result in zip(["tsx", "js", "json"], upload_results) if result is None]
        print(f"Failed to upload the following files: {', '.join(failed_uploads)}")
        await set_component_status(component_id, "failed")
    
    # Clean up temporary files
    for file_path in [temp_tsx_path, temp_js_path, temp_json_path]:
        try:
            os.remove(file_path)
        except FileNotFoundError:
            print(f"Warning: Could not delete {file_path} as it was not found.")

    return code_block_content


# Web endpoint for generating code
@app.function(timeout = 60 * 15)
@modal.web_endpoint(method="POST")
async def generate_code_api(input: InputGenerateCode):
    await generate_code.remote(input.user_id, input.what_and_why, input.s3_file_path, input.component_id)

# Input model for get_status_api
class InputGetStatus(BaseModel):
    component_id: str

# Function to get job status
# @app.function(image=image)
# def get_status(component_id: str) -> str:
#     return job_statuses.get(component_id, "not_found")

# # Web endpoint for getting status
# @app.function()
# @modal.web_endpoint(method="POST")
# def get_status_api(input: InputGetStatus):
#     return get_status.remote(input.component_id)

# Input model for set_status_api
class InputSetStatus(BaseModel):
    component_id: str
    status: str

# Function to set job status
@app.function(image=image)
def set_status(component_id: str, status: str):
    job_statuses[component_id] = status

# Web endpoint for setting status
@app.function()
@modal.web_endpoint(method="POST")
def set_status_api(input: InputSetStatus):
    set_status.remote(input.component_id, input.status)
    print("done")
    return {"message": "Status set successfully"}
