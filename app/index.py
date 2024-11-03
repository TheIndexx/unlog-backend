from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Header, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import csv
import json
import requests
import os
import time
from typing import List, Dict, Any, Union
import chardet
import re
import uvicorn
import uuid
import subprocess
from clerk import Client
import logging
import asyncio
from clerk.types import UpdateUserRequest, User
from typing import Dict, Any
from dotenv import load_dotenv
import asyncio
from fastapi import Header, HTTPException
from clerk import Client
from utils import clean_key, clean_value, User, VisualizeRequest, FetchComponentRequest
from functions import get_current_user, reduce_user_credits, csv_to_json, anthropic_api_call, upload_to_s3, read_from_s3, get_user_ui_names, fetch_component_status, set_component_status, call_generate_code_api, update_user_paid_status
from ssl import SSLCertVerificationError
import modal
from modal import Function
import aiohttp
from urllib.parse import urlencode
from fastapi import BackgroundTasks
from prompts import first_prompt, second_prompt, third_prompt
import boto3
from botocore.exceptions import ClientError
from stripe import StripeClient
import tempfile

app = FastAPI(debug=True)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Load environment variables from .env.local file
load_dotenv('.env.local')

# Get the value of the ANTHROPIC_API_KEY from environment variables
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
CLERK_SECRET_KEY = os.getenv('CLERK_SECRET_KEY')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ID')
print("ANTHROPIC_API_KEY: ", ANTHROPIC_API_KEY)
print("CLERK_SECRET_KEY: ", CLERK_SECRET_KEY)

UPLOAD_FOLDER = './uploads'
COMPONENT_FOLDER = './components'
stripe = StripeClient(os.getenv('STRIPE_SECRET_KEY'))

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(COMPONENT_FOLDER, exist_ok=True)


@app.get("/api/user/private-metadata")
async def get_user_private_metadata(current_user: User = Depends(get_current_user)):
    print("in get_user_private_metadata")
    try:
        client = Client(CLERK_SECRET_KEY)
        async with client:
            user = await client.users.get(current_user.id)
            # print("user: ", user)
            return JSONResponse(content={
                "privateMetadata": user.private_metadata,
            }, status_code=200)

    except Exception as e:
        logger.error(f"Error fetching private metadata for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching private metadata")
    
# Example usage in a FastAPI route
@app.post("/reduce-credits")
async def reduce_credits(user_id: str):
    result = await reduce_user_credits(user_id)
    if result["success"]:
        return {"message": result["message"]}
    else:
        raise HTTPException(status_code=400, detail=result["message"])

@app.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    return {"message": f"Hello, {current_user.first_name}!"}

@app.get("/public")
async def public_route():
    return {"message": "This is a public route"}


@app.get("/")
def read_main():
    return {"message": "Hello, welcome to the visualization API"}

# @app.post("/api/upload")
# async def upload_file(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
#     if not file:
#         raise HTTPException(status_code=400, detail="No file part")

#     # Check if the user is a paid user
#     print("current_user: ", current_user)
#     client = Client(CLERK_SECRET_KEY)
    
#     async with client:
#         try:
#             user = await client.users.get(current_user.id)
#             print("user: ", user.__dict__)
#             is_paid_user = user.private_metadata.get('isPaidUser', False)

#             if not is_paid_user:
#                 # For non-paid users, check credits
#                 credits = user.private_metadata.get('credits', 0)
#                 if credits <= 0:
#                     raise HTTPException(status_code=403, detail="You have no credits left")

#             filename = f"{user.id}_{file.filename}"  # Prepend user ID to filename
#             file_path = os.path.join(UPLOAD_FOLDER, filename)
#             content = await file.read()
#             with open(file_path, "wb") as buffer:
#                 buffer.write(content)

#             return JSONResponse(content={"filePath": file_path}, status_code=200)
#         except Exception as e:
#             print(f"Error in upload_file: {str(e)}")
#             raise HTTPException(status_code=500, detail=f"An error occurred during file upload: {str(e)}")


@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...), 
    component_name: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    if not file:
        raise HTTPException(status_code=400, detail="No file part")

    print("current_user: ", current_user)
    client = Client(CLERK_SECRET_KEY)
    
    async with client:
        try:
            user = await client.users.get(current_user.id)
            # print("user: ", user.__dict__)
            is_paid_user = user.private_metadata.get('isPaidUser', False)

            if not is_paid_user:
                credits = user.private_metadata.get('credits', 0)
                if credits <= 0:
                    raise HTTPException(status_code=403, detail="You have no credits left")

            filename = f"{component_name}_{user.id}_{file.filename}"  # Include component name and user ID in filename
            content = await file.read()
            
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name

            # Upload to S3
            s3_key_folder = f"{user.id}/{component_name}"  # Include component name in the folder structure
            s3_path = upload_to_s3(temp_file_path, S3_BUCKET_NAME, s3_key_folder, filename, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)

            # Remove the temporary file
            os.unlink(temp_file_path)

            if s3_path:
                print(f"File successfully uploaded to S3: {s3_path}")
                return JSONResponse(content={"filePath": s3_path}, status_code=200)
            else:
                print("S3 upload failed: s3_path is None or empty")
                raise HTTPException(status_code=500, detail="Failed to upload file to S3")
        except Exception as e:
            print(f"Error in upload_file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"An error occurred during file upload: {str(e)}")


@app.get("/api/full-data/{component_id}")
async def get_full_data(component_id: str, current_user: User = Depends(get_current_user)):
    json_file_path = os.path.join(COMPONENT_FOLDER, f"{component_id}.json")
    if os.path.exists(json_file_path):
        with open(json_file_path, "r") as f:
            data = json.load(f)
        return data
    else:
        raise HTTPException(status_code=404, detail="Data not found")     

@app.post("/api/visualize")
async def visualize(request: dict, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user)):
    what_and_why = request['what_and_why']
    s3_file_path = request['input_file']
    component_name = request.get('component_name')
    print("in api/visualize: ", what_and_why, s3_file_path, component_name)
    if not all([what_and_why, s3_file_path]):
        raise HTTPException(status_code=400, detail="Missing required parameters")

    component_id = component_name
    await set_component_status(component_id, "pending")

    background_tasks.add_task(call_generate_code_api, current_user.id, what_and_why, s3_file_path, component_id)


    status_response = await set_component_status(component_id, "pending")
    print("status_response: ", status_response)
    
    if not current_user.is_paid_user:
        try:
            # Reduce user credits only for non-paid users
            credit_reduction_result = await reduce_user_credits(current_user.id)
            if not credit_reduction_result['success']:
                logger.warning(f"Failed to reduce user credits: {credit_reduction_result['message']}")
        except Exception as e:
            logger.error(f"Error reducing user credits: {str(e)}")
    
    return JSONResponse(content={
        "message": "The visualization component is being generated.",
        "component_id": component_id,
    }, status_code=200)
    
    
@app.post("/api/fetch-component")
async def fetch_component(request: FetchComponentRequest, current_user: User = Depends(get_current_user)):
    component_id = request.component_id
    user_id = current_user.id
    
    # Check the status of the component
    status = await fetch_component_status(component_id, user_id)
    print("status: ", status)
        
    if status == "completed":
        # Fetch the generated code
        s3_bucket = os.environ.get('S3_BUCKET_NAME')
        s3_key_folder = os.path.join(str(user_id), component_id)
        s3_key = f"{component_id}"
        
        code_content = read_from_s3(s3_bucket, s3_key_folder, f"{s3_key}.tsx",  AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
        if code_content is None:
            raise HTTPException(status_code=404, detail=f"Component not found: {component_id}")

        compiled_code = read_from_s3(s3_bucket, s3_key_folder, f"{s3_key}.js", AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
        if compiled_code is None:
            raise HTTPException(status_code=500, detail="Error fetching compiled component")

        json_content = read_from_s3(s3_bucket, s3_key_folder, f"{s3_key}.json", AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
        json_data = json.loads(json_content) if json_content else None

        return JSONResponse(content={
            "message": "Component fetched successfully",
            "component_id": component_id,
            "tsx_code": code_content,
            "compiled_code": compiled_code,
            "json_data": json_data
        }, status_code=200)
    elif status == "pending":
        return JSONResponse(content={"status": "pending"}, status_code=202)
    else:
        raise HTTPException(status_code=500, detail="Error checking component status")

class StatusRequest(BaseModel):
    component_id: str
    
@app.post("/api/check-component-status")
async def check_component_status(request: StatusRequest, current_user: str = Depends(get_current_user)):
    
    
    s3_client = boto3.client('s3',
        aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['AWS_SECRET_ID']
    )
    
    s3_bucket = os.environ.get('S3_BUCKET_NAME')
    s3_key_folder = os.path.join(str(current_user.id), request.component_id)
    
    files_to_check = [
        # f"{request.component_id}.tsx",
        f"{request.component_id}.js",
        # f"{request.component_id}.json"
    ]
    print("BEFORE TRY")
    try:
        for file in files_to_check:
            s3_key = f"{s3_key_folder}/{file}"
            print("s3_key: ", s3_key)
            try:
                s3_client.head_object(Bucket=s3_bucket, Key=s3_key)
                print("SUCCESS")
            except ClientError as e:
                if e.response['Error']['Code'] == "404":
                    print("PENDING")
                    
                    return "pending"
                else:
                    print("FAIL")
                    
                    raise HTTPException(status_code=500, detail="Error checking S3")
        
        return "completed"
    
    except Exception as e:
        print(f"Error checking S3 for component status: {str(e)}")
        return "error"


class CheckoutSessionRequest(BaseModel):
    priceId: str
    userId: str


@app.post("/api/create-checkout-session")
async def create_checkout_session(
    request: CheckoutSessionRequest,
    current_user: dict = Depends(get_current_user)
):
    print("IN REQ")
    
    if current_user.id != request.userId:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    print("os.getenv('NEXT_PUBLIC_SITE_URL'): ", os.getenv('NEXT_PUBLIC_SITE_URL'))
    
    try:
        client = Client(CLERK_SECRET_KEY)
        user = client.users.get(request.userId)
        session = stripe.checkout.sessions.create(
        params={
                "mode": "subscription",
                "line_items": [{
                    "price": request.priceId,
                    "quantity": 1,
                }],
                "success_url": f"{os.getenv('NEXT_PUBLIC_SITE_URL')}",
                "cancel_url": os.getenv('NEXT_PUBLIC_SITE_URL'),
                # "customer_email": user.email_addresses[0].email_address if user.email_addresses else None,
                "client_reference_id": request.userId,
            }
        )
        
        # Update user status to paid
        try:
            update_result = await update_user_paid_status(request.userId, True)
            if not update_result['success']:
                print(f"Warning: {update_result['message']}")
                # You might want to log this warning or handle it in some way

            return {"checkoutUrl": session.url}
        except Exception as e:
            print(f"Error creating checkout session: {str(e)}")
            raise HTTPException(status_code=500, detail=f"An error occurred while creating the checkout session: {str(e)}")


    except Exception as e:
        print(f"Error creating checkout session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred while creating the checkout session: {str(e)}")

async def handle_successful_payment(session):
    user_id = session.get('client_reference_id')
    if not user_id:
        print("No user_id found in session")
        return

    try:
        client = Client(CLERK_SECRET_KEY)
        
        user = client.users.get(user_id)
        client.users.update(user_id,
            private_metadata={
                **user.private_metadata,
                "isPaidUser": True,
                "credits": None  # Remove credits for paid users
            }
        )
        print(f"User {user_id} successfully upgraded to paid status")
    except Exception as e:
        print(f"Error updating user {user_id} to paid status: {str(e)}")
        
    
@app.get("/api/list-user-uis")
async def list_user_uis(current_user: User = Depends(get_current_user)):
    print("\n--- Starting /api/list-user-uis ---")
    user_id = str(current_user.id)
    print(f"Listing UIs for user: {user_id}")

    ui_names = get_user_ui_names(user_id)

    print("--- Finishing /api/list-user-uis ---")
    return JSONResponse(content={
        "message": "User UIs listed successfully",
        "ui_names": ui_names
    }, status_code=200)
    

@app.get("/get-code/{component_id}")
async def get_code(component_id: str, current_user: User = Depends(get_current_user)):
    component_path = os.path.join(COMPONENT_FOLDER, f"{component_id}.tsx")
    
    if os.path.exists(component_path):
        with open(component_path, "r") as f:
            code_content = f.read()
        return {"code": code_content}
    else:
        raise HTTPException(status_code=404, detail="Code not found")


def extract_code_block(text: str, current_user: User = Depends(get_current_user)) -> str:
    start = text.find("```tsx")
    if start != -1:
        end = text.find("```", start + 6)
        if end != -1:
            return text[start + 6:end].strip()
    return ""

if __name__ == '__main__':
    uvicorn.run(app, host="127.0.0.1", port=8000)
    
    

# use later in production
# @app.post("/webhook")
# async def stripe_webhook(request: Request):
#     payload = await request.body()
#     sig_header = request.headers.get("Stripe-Signature")

#     try:
#         event = stripe.webhooks.construct_event(
#             payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET')
#         )
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail="Invalid payload")
#     except stripe.error.SignatureVerificationError as e:
#         raise HTTPException(status_code=400, detail="Invalid signature")

#     if event['type'] == 'checkout.session.completed':
#         session = event['data']['object']
#         await handle_successful_payment(session)

#     return {"status": "success"}
