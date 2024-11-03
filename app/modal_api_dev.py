import os
import json
import modal
from modal import Image, Secret, App, Dict
from functions import get_current_user, reduce_user_credits, anthropic_api_call, upload_to_s3, read_from_s3, get_user_ui_names, extract_code_block, fetch_component_status, set_component_status, anthropic_api_call_data_cleaner, update_component_privacy
from prompts import first_prompt, second_prompt, third_prompt
from prompt_new import first_prompt, prompt_templates, determine_path, data_cleaner
from dotenv import load_dotenv
from pydantic import BaseModel
from preprocessing import csv_to_json, clean_key, to_camel_case, clean_value, standardize_data_types, handle_missing_values, normalize_strings, handle_currency, json_to_csv, sample_df_with_char_limit
import pandas as pd
import random
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Header
import io
from io import StringIO, BytesIO

load_dotenv('.env.local')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ID = os.getenv('AWS_SECRET_ID')
import subprocess
print("AWS_ACCESS_KEY_ID", AWS_ACCESS_KEY_ID)
print("AWS_SECRET_ID", AWS_SECRET_ID)
# Define image with necessary dependencies
image = (
    Image.debian_slim(python_version="3.11.9")
    .pip_install("anthropic", "python-dotenv", "boto3", "chardet", "uvicorn", "clerk-sdk-python", "awscli", "pandas", "tenacity", "openpyxl")
    .apt_install("nodejs", "npm")
    .run_commands(
        "mkdir -p /app",
        "cd /app && npm init -y",
        "cd /app && npm install @babel/core @babel/cli @babel/preset-env @babel/preset-react @babel/preset-typescript"
    )
    .copy_local_file(".babelrc", "/app/.babelrc")
)

S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
# S3_BUCKET_NAME = "code-file-storage"

# Define main Modal app
app = modal.App("code-generation-app", image=image)

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
    


@app.function(image=image, secrets=[Secret.from_name("ANTHROPIC_API_KEY"), Secret.from_name("my-aws-secret"), Secret.from_name("clerk-secret-key")])
async def generate_code(user_id, what_and_why, s3_file_path, component_id):
    AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
    AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
    ANTHROPIC_API_KEY = os.environ['ANTHROPIC_API_KEY']
    AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
    AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
    print("os.environ['CLERK_SECRET_KEY']: ", os.environ['CLERK_SECRET_KEY'])
    CLERK_SECRET_KEY = os.environ['CLERK_SECRET_KEY']
    print(" AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY: ",  AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    S3_BUCKET_NAME = os.environ['S3_BUCKET_NAME']
    # Extract bucket name, folder, and key from s3_file_path
    _, _, bucket, s3_key = s3_file_path.split('/', 3)
    s3_key_folder, s3_key = os.path.split(s3_key)
    
    json_data = csv_to_json(bucket, s3_key_folder, s3_key, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    csv_data = json_to_csv(json_data)
    csv_data_io = io.StringIO(csv_data)
    df = pd.read_csv(csv_data_io, thousands=',')
    sample_df, data_sample_str_csv = sample_df_with_char_limit(df)
    num_rows = len(df)
    
    data_cleaner_response = anthropic_api_call_data_cleaner(data_cleaner, ANTHROPIC_API_KEY)
    data_cleaner_code = extract_code_block(data_cleaner_response, 'python')
    
    
    if not data_cleaner_code:
        data_cleaner_code = extract_code_block(data_cleaner_response, 'py')
        if not data_cleaner_code:
            data_cleaner_code = data_cleaner_response
            print("FAILED AND DIDNT EXEC PYTHON")

    preprocessing_successful = False

    try:
        # Execute the data_cleaner_code
        exec(data_cleaner_code)
        
        # Retrieve the cleaned DataFrame
        # cleaned_df = local_namespace['df']f
        
        # Check if the cleaned DataFrame is valid and has the same number of rows
        # df = cleaned_df
        preprocessing_successful = True
        print("Data cleaning executed successfully.")
    
    except Exception as e:
        print(f"An error occurred while executing data cleaning code: {str(e)}")
        print("Continuing with the original DataFrame without preprocessing.")

    # Continue with the rest of your function...
    if preprocessing_successful:
        print("Using preprocessed data for further operations.")
    else:
        print("Using original data for further operations.")
        # df = original_df
            
                
    
    print(f'Processing code: {data_cleaner_code}')
    
    sample_size = min(20, len(json_data))
    data_sample_json = random.sample(json_data, sample_size)
    data_sample_json_str = json.dumps(data_sample_json, indent=2)   
    
    
    formatted_first_prompt = first_prompt.format(
        what_and_why=what_and_why,
        json_data=json.dumps(json_data[:5], indent=2)
    )
    
    
    first_response = anthropic_api_call(formatted_first_prompt, ANTHROPIC_API_KEY)
    print("first_response: ", first_response)
    if not first_response:
        raise HTTPException(status_code=500, detail="Failed to get a response from the first API call.")
    
    
    chosen_path = determine_path(first_response)
     
    second_prompt_template = prompt_templates[chosen_path]["second_prompt"]
    third_prompt_template = prompt_templates[chosen_path]["third_prompt"]
    
    
    formatted_second_prompt = second_prompt_template.format(
            what_and_why=what_and_why,
            first_response=first_response,
            json_data=json.dumps(json_data[:5], indent=2),
            num_rows= len(df)
        )
    
    second_response = anthropic_api_call(formatted_second_prompt, ANTHROPIC_API_KEY)
    print("second_response: ", second_response)
    
    if not second_response:
        raise HTTPException(status_code=500, detail="Failed to get a response from the second API call.")
    
    
    third_prompt_formatted = third_prompt_template.format(
            what_and_why=what_and_why,
            first_response=first_response,
            second_response=second_response,
            json_data=json.dumps(json_data[:5], indent=2),
            num_rows= len(df)
        )
    
    third_response = anthropic_api_call(third_prompt_formatted, ANTHROPIC_API_KEY)
    print("third_response: ", third_response)
    
    code_block_content = extract_code_block(third_response, 'jsx')
    
    
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
        upload_to_s3(temp_tsx_path, S3_BUCKET_NAME, s3_key_folder, f"{component_id}.tsx", AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY),
        upload_to_s3(temp_js_path, S3_BUCKET_NAME, s3_key_folder, f"{component_id}.js", AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY),
        upload_to_s3(temp_json_path, S3_BUCKET_NAME, s3_key_folder, f"{component_id}.json", AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
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
@app.function()
@modal.web_endpoint(method="POST")
async def generate_code_api_dev(input: InputGenerateCode):
    await generate_code.remote(input.user_id, input.what_and_why, input.s3_file_path, input.component_id)

# Input model for get_status_api
class InputGetStatus(BaseModel):
    component_id: str

# Function to get job status
@app.function(image=image)
def get_status(component_id: str) -> str:
    return job_statuses.get(component_id, "not_found")

# Web endpoint for getting status
@app.function()
@modal.web_endpoint(method="POST")
def get_status_api_dev(input: InputGetStatus):
    return get_status.remote(input.component_id)

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
def set_status_api_dev(input: InputSetStatus):
    set_status.remote(input.component_id, input.status)
    print("done")
    return {"message": "Status set successfully"}
