from fastapi import HTTPException, Header
import csv
import requests
import os
from typing import List, Dict, Any
import chardet
import re
from clerk import Client
import logging
import asyncio
from typing import Dict, Any
from dotenv import load_dotenv
import asyncio
from fastapi import Header, HTTPException
from clerk import Client
from utils import clean_key, clean_value, User
from ssl import SSLCertVerificationError
import boto3
import aiohttp
load_dotenv('.env.local')
from botocore.exceptions import ClientError
from textwrap import dedent
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential
import asyncio
import ssl
import certifi
# from svix.webhooks import Webhook, WebhookVerificationError

import pathlib
BASE_DIR = pathlib.Path(__file__).resolve().parent
env_path = BASE_DIR / ".env.local"
load_dotenv(env_path)


ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
CLERK_SECRET_KEY = os.getenv('CLERK_SECRET_KEY')


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CustomClient(Client):
    def __init__(self, token: str, base_url: str = "https://api.clerk.dev/v1/", timeout_seconds: float = 30.0) -> None:
        # Create SSL context with certifi certificates
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        
        # Initialize session with SSL context
        self._session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {token}"},
            timeout=aiohttp.ClientTimeout(total=timeout_seconds),
            connector=aiohttp.TCPConnector(ssl=ssl_context)
        )
        self._base_url = base_url

async def get_current_user(x_user_id: str = Header(...)) -> User:
    logger.info(f"Attempting to authenticate user with ID: {x_user_id}")
    
    try:
        # This is a workaround bc SSL cert errors with CustomClient
        client = CustomClient(CLERK_SECRET_KEY)
        # original code: client = Client(CLERK_SECRET_KEY)
       
        async with client:
            user = None
            for attempt in range(3):  # Try up to 3 times
                try:
                    print(1)
                    user = await client.users.get(x_user_id)
                    print(2)
                    logger.info(f"Retrieved user data backend_app: {user}")
                    is_paid_user = user.private_metadata.get('isPaidUser', False)
                    
                    if user.private_metadata:
                        logger.info(f"Private metadata found: {user.private_metadata}")
                        break
                    
                    logger.info(f"No Private metadata found, attempt {attempt + 1}/3")
                    if attempt < 2:  # Don't sleep on the last attempt
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                except Exception as e:
                    logger.error(f"Error on attempt {attempt + 1}: {str(e)}")
                    if attempt == 2:  # Last attempt
                        raise  # Re-raise the last exception
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found after multiple attempts")
            
            if not user.private_metadata:
                logger.warning(f"No private metadata found for user {x_user_id} after all attempts")
            
            return User(
                id=user.id,
                first_name=user.first_name,
                last_name=user.last_name or '',
                email_address=user.email_addresses[0].email_address if user.email_addresses else None,
                credits=user.private_metadata.get('credits', 0),
                is_paid_user=is_paid_user
            )
    except SSLCertVerificationError as e:
        logger.error(f"SSL Certificate Verification Error: {str(e)}")
        raise HTTPException(status_code=500, detail="SSL certificate verification failed")
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Unexpected error for user ID {x_user_id}. Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    

async def reduce_user_credits(user_id: str, credits_to_reduce: int = 1) -> Dict[str, Any]:
    
    async with CustomClient(CLERK_SECRET_KEY) as client:
        try:
            # Fetch the current user data
            user: User = await client.users.get(user_id)
            
            # Check if credits exist in private metadata
            current_credits = user.private_metadata.get('credits')
            
            if current_credits is None:
                return {"success": False, "message": "No credits found for user"}
            
            if current_credits < credits_to_reduce:
                return {"success": False, "message": f"User does not have enough credits. Current balance: {current_credits}, Attempted to reduce: {credits_to_reduce}"}
            
            # Reduce credits by specified amount
            new_credits = current_credits - credits_to_reduce
            
            # Prepare the update payload
            update_payload = {
                "private_metadata": {
                    **user.private_metadata,
                    "credits": new_credits
                }
            }
            
            # Update user's private metadata
            async with client.patch(f"users/{user_id}", json=update_payload) as response:
                if response.status == 200:
                    updated_user_data = await response.json()
                    updated_credits = updated_user_data.get('private_metadata', {}).get('credits')
                    if updated_credits == new_credits:
                        return {
                            "success": True, 
                            "message": f"Credits reduced successfully. New balance: {new_credits}"
                        }
                    else:
                        return {
                            "success": False, 
                            "message": "Failed to update credits. Please try again."
                        }
                else:
                    error_data = await response.json()
                    return {
                        "success": False,
                        "message": f"Failed to update credits. Status: {response.status}, Error: {error_data}"
                    }
                
        except Exception as e:
            print(f"Error reducing credits: {str(e)}")
            return {"success": False, "message": f"Error reducing credits: {str(e)}"}


async def add_user_credits(user_id: str, credits_to_add: int = 1) -> Dict[str, Any]:
    async with CustomClient(CLERK_SECRET_KEY) as client:
        try:
            # Fetch the current user data
            user: User = await client.users.get(user_id)
            
            # Get current credits (default to 0 if none exist)
            current_credits = user.private_metadata.get('credits', 0)
            
            # Add new credits to existing credits
            new_credits = current_credits + credits_to_add
            
            # Prepare the update payload
            new_metadata = user.private_metadata.copy()
            new_metadata['credits'] = new_credits
            
            update_payload = {
                "private_metadata": new_metadata
            }
            
            # Update user's private metadata
            async with client.patch(f"users/{user_id}", json=update_payload) as response:
                if response.status == 200:
                    updated_user_data = await response.json()
                    updated_credits = updated_user_data.get('private_metadata', {}).get('credits')
                    if updated_credits == new_credits:
                        return {
                            "success": True,
                            "message": f"Credits added successfully. New balance: {new_credits}"
                        }
                    else:
                        return {
                            "success": False,
                            "message": "Failed to add credits. Please try again."
                        }
                else:
                    error_data = await response.json()
                    return {
                        "success": False,
                        "message": f"Failed to add credits. Status: {response.status}, Error: {error_data}"
                    }
                    
        except Exception as e:
            print(f"Error adding credits: {str(e)}")
            return {"success": False, "message": f"Error adding credits: {str(e)}"}



async def grant_initial_credits(user_id: str) -> Dict[str, Any]:
    async with CustomClient(CLERK_SECRET_KEY) as client:
        try:
            user: User = await client.users.get(user_id)
            new_metadata = user.private_metadata.copy()
            new_metadata['credits'] = 5
            new_metadata['isPaidUser'] = False
            # Check if credits already exist in private metadata
            update_payload = {
                "private_metadata": new_metadata
            }
            
            # Update user's private metadata
            async with client.patch(f"users/{user_id}", json=update_payload) as response:
                if response.status == 200:
                    return {
                            "success": True, 
                            "message": f"User credits updated successfully to 5"
                        }
                else:
                    error_data = await response.json()
                    return {
                        "success": False,
                        "message": f"Failed to add crdits. Status: {response.status}, Error: {error_data}"
                    }
                
        except Exception as e:
            print(f"Error granting initial credits: {str(e)}")
            return {"success": False, "message": f"Error granting initial credits: {str(e)}"}
        

def csv_to_json(csv_file_path: str) -> List[Dict[str, Any]]:
    # csv_file_path = csv_file_path[1:]
    
    # Detect file encoding
    with open(csv_file_path, 'rb') as raw_file:
        result = chardet.detect(raw_file.read())
    
    # Try detected encoding, fall back to 'latin-1' if it fails
    encodings_to_try = [result['encoding'], 'latin-1', 'iso-8859-1']
    
    for encoding in encodings_to_try:
        try:
            with open(csv_file_path, 'r', encoding=encoding, errors='replace') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                json_data = []
                for row in csv_reader:
                    processed_row = {
                        clean_key(key): clean_value(value)
                        for key, value in row.items()
                    }
                    json_data.append(processed_row)
                
                if json_data:
                    fields = list(json_data[0].keys())
                    # First, identify which fields have non-null values in any row
                    non_null_fields = set()
                    for item in json_data:
                        for field in fields:
                            if item[field] is not None:
                                non_null_fields.add(field)
                    
                    # Then, filter rows, keeping only those that have non-null values for all fields in non_null_fields
                    filtered_json_data = []
                    for item in json_data:
                        if all(item[field] is not None for field in non_null_fields):
                            filtered_json_data.append(item)
                    
                    json_data = filtered_json_data
                
                return json_data
        except UnicodeDecodeError:
            print(f"Failed to decode with {encoding}, trying next encoding...")
        except Exception as e:
            print(f"Error in csv_to_json: {str(e)}")
    
    print("Failed to decode the file with all attempted encodings.")
    return []

def anthropic_api_call(content: str, ANTHROPIC_API_KEY):
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "content-type": "application/json",
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "max-tokens-3-5-sonnet-2024-07-15"
    }
    data = {
        "model": "claude-3-5-sonnet-20240620",
        "max_tokens": 8192,
        # "system": "You are part of a system named SpreadSite. A pipeline that allows users to turn their spreadsheets into custom built websites to visualize their spreadsheets in a more intuitive way. The problem is so many people do work on spreadsheets and spreadsheets suck. You are here to execute your role to make sure interfacing with spreadsheet data does not suck anymore. The user is relying on your work being a single state of truth. That means you cannot build anything that is pretend or fake or beyond the scope of single truth.", 
        "system": f"""You are part of a system named SpreadSite. A pipeline that allows users to turn their spreadsheets into custom built websites to visualize their spreadsheets in a more intuitive way. The problem is data is spreadsheet data is difficult to understand and interact with. You are here to execute your role to make sure interfacing with spreadsheet data does not suck anymore. You are the Steve Jobs mixed with Edward Tufte of data interfacing, making it simple and easy for one to interface with their data. Your outputs must always be at least 6,000 tokens long and at most 7,500 tokens long, no matter what. Never use: Date Picker, PieCharts, ScatterChart, Tooltip, TreeMap Radian Charts and theme provider. I expect the javascripts to have around hundreds of lines of inline CSS to make them look like stripe dashboards. Everything must stay reliable and in scope or else you will break the product. If functionality is expected of you, the functionality must work no matter what.
        Important constraints: Make sure your response is under 700 lines of code. Don't you dare to use any components that need installed dependencies besides shadcn, rechart, lucide, react-simple-maps and tremor. Your website cannot have any actions built for them to take beyond actions that are possible with link clicks. Everything must be built with the expectation everything is limited to the browser and pre-installed components. That does not mean you should not maximize what interactivity/ data exploration could happen within its constraints. The entire website must be fully functional and working with nothing being non functional.""",
        "messages": [
            {"role": "user", "content": dedent(content)}
        ]
    }
    
    try:
        print("IN ANTHROPIC API CALL")
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result['content'][0]['text'] or 'No response'
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while calling the Anthropic API: {e}")
    except KeyError:
        print("Unexpected response format from Anthropic API")
    return 'Error occurred'

def anthropic_api_call_data_cleaner(content: str, ANTHROPIC_API_KEY):
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "content-type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    data = {
        "model": "claude-3-5-sonnet-20240620",
        "max_tokens": 4000,
        # "system": "You are part of a system named SpreadSite. A pipeline that allows users to turn their spreadsheets into custom built websites to visualize their spreadsheets in a more intuitive way. The problem is so many people do work on spreadsheets and spreadsheets suck. You are here to execute your role to make sure interfacing with spreadsheet data does not suck anymore. The user is relying on your work being a single state of truth. That means you cannot build anything that is pretend or fake or beyond the scope of single truth.", 
        
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

def upload_to_s3(file_path, bucket_name, s3_key_folder, s3_key, AWS_ACCESS_KEY_ID, AWS_SECRET_ID, region='us-east-1'):
    print(f"Starting upload process for file: {file_path}")
    
    print("AWS_ACCESS_KEY_ID", AWS_ACCESS_KEY_ID)
    print("AWS_SECRET_ID", AWS_SECRET_ID)
    
    print(f"Creating S3 resource for region: {region}")
    try:
        s3_resource = boto3.resource(
            's3', 
            region_name=region, 
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ID
        )
        print("S3 resource created successfully")
    except Exception as e:
        print(f"Failed to create S3 resource: {e}")
        return None
    
    full_s3_key = os.path.join(s3_key_folder, s3_key)
    print(f"Full S3 key: {full_s3_key}")
    
    print(f"Attempting to upload file to bucket: {bucket_name}")
    try:
        with open(file_path, 'rb') as file:
            s3_resource.Bucket(bucket_name).put_object(
                Key=full_s3_key, 
                Body=file
            )
        print(f"File {file_path} uploaded successfully to {bucket_name}/{full_s3_key}")
        return f"s3://{bucket_name}/{full_s3_key}"
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
    except boto3.exceptions.S3UploadFailedError as e:
        print(f"Error: S3 upload failed. {e}")
    except Exception as e:
        print(f"Failed to upload {file_path} to {bucket_name}/{full_s3_key}: {e}")
    return None

def read_from_s3(bucket_name, s3_key_folder, s3_key, AWS_ACCESS_KEY_ID, AWS_SECRET_ID, region='us-east-1'):
    # Load environment variables from .env.local
    load_dotenv('.env.local')

    # # Get AWS credentials from environment variables
    # AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    # AWS_SECRET_ID = os.getenv('AWS_SECRET_ID')

    print("AWS_ACCESS_KEY_ID: ", AWS_ACCESS_KEY_ID)
    print("AWS_SECRET_ID: ", AWS_SECRET_ID)
    # Create an S3 client
    s3_client = boto3.client(
        's3', 
        region_name=region, 
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ID
    )
    
    # Combine the folder and file name to create the full S3 key
    full_s3_key = os.path.join(s3_key_folder, s3_key)
    print("full_s3_key: ", full_s3_key)
    # Read the file from S3
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=full_s3_key)
        file_content = response['Body'].read().decode('utf-8')
        print(f"File {full_s3_key} read from {bucket_name}")
        return file_content
    except Exception as e:
        print(f"Failed to read {full_s3_key} from {bucket_name}: {e}")
        return None

    
def get_user_ui_names(user_id: str):
    # Load environment variables from .env.local
    load_dotenv('.env.local')

    # Get AWS credentials and S3 bucket name from environment variables
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ID = os.getenv('AWS_SECRET_ID')
    S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

    # Create an S3 client
    s3_client = boto3.client(
        's3', 
        region_name='us-east-1', 
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ID
    )

    print('in GET CURRENT')
    # List objects in the user's folder
    try:
        response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET_NAME,
            Prefix=f"{user_id}/"
        )

        # Extract UI names and creation dates from the object keys
        ui_info = []
        for obj in response.get('Contents', []):
            key = obj['Key']
            # The key format is expected to be "{user_id}/{component_id}.{extension}"
            parts = key.split('/')
            if len(parts) == 3 and parts[2].endswith('.js'):
                ui_name = parts[1]
                created_date = obj['LastModified']
                ui_info.append({"name": ui_name, "created": created_date})
        
        # Sort ui_info by created date in descending order
        ui_info.sort(key=lambda x: x['created'], reverse=True)
        
        # Convert datetime objects to ISO format strings
        for item in ui_info:
            item['created'] = item['created'].isoformat()
        
        return ui_info
    except Exception as e:
        print(f"Failed to list objects for user {user_id}: {e}")
        return []


async def update_user_prompts(user_id: str, component_id: str, user_prompt: str) -> Dict[str, Any]:
    async with Client(CLERK_SECRET_KEY) as client:
        try:
            # Fetch the current user data
            user: User = await client.users.get(user_id)
            
            # Get the current prompts from private metadata
            current_prompts = user.private_metadata.get('prompts', {})
            
            # Update the prompts dictionary
            current_prompts[component_id] = user_prompt
            
            # Prepare the update payload
            update_payload = {
                "private_metadata": {
                    **user.private_metadata,
                    "prompts": current_prompts
                }
            }
            
            # Update user's private metadata
            async with client.patch(f"users/{user_id}", json=update_payload) as response:
                if response.status == 200:
                    return {"success": True, "message": "User prompts updated successfully."}
                else:
                    error_data = await response.json()
                    return {
                        "success": False,
                        "message": f"Failed to update user prompts. Status: {response.status}, Error: {error_data}"
                    }
                
        except Exception as e:
            print(f"Error updating user prompts: {str(e)}")
            return {"success": False, "message": f"Error updating user prompts: {str(e)}"}


def extract_code_block(text: str, lang: str) -> str:
    pattern = re.compile(rf'```{lang}(.*?)```', re.DOTALL)
    matches = pattern.findall(text)
    return max(matches, key=len, default='').strip() if matches else ''


async def fetch_component_status(component_id, user_id):
    s3_client = boto3.client('s3',
        aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['AWS_SECRET_ID']
    )
    print("os.environ['AWS_ACCESS_KEY_ID']", os.environ['AWS_ACCESS_KEY_ID'])
    print("os.environ['AWS_SECRET_ID']", os.environ['AWS_SECRET_ID'])
    s3_bucket = os.environ.get('S3_BUCKET_NAME')
    print("s3_bucket: ", s3_bucket)
    s3_key_folder = os.path.join(str(user_id), component_id)
    print("component_id: ", component_id)
    files_to_check = [
        f"{component_id}.tsx",
        f"{component_id}.js",
        f"{component_id}.json"
    ]
    
    try:
        for file in files_to_check:
            s3_key = f"{s3_key_folder}/{file}"
            print("s3_key: ", s3_key)
            
            try:
                s3_client.head_object(Bucket=s3_bucket, Key=s3_key)
            except ClientError as e:
                if e.response['Error']['Code'] == "404":
                    # If any file is missing, the component is not complete
                    return "pending"
                else:
                    # If there's another error, raise it
                    raise
        
        # If we've checked all files and they exist, the component is complete
        return "completed"
    
    except Exception as e:
        print(f"Error checking S3 for component status: {str(e)}")
        return "error"
        
        


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def set_component_status(component_id, status):
    async with aiohttp.ClientSession() as session:
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        url = os.getenv('MODAL_SETSTATUS')
        
        payload = {"component_id": component_id, "status": status}
        
        try:
            async with session.post(url, json=payload, headers=headers, timeout=10) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"Error response (status {response.status}): {error_text}")
                    raise HTTPException(status_code=response.status, detail=f"Failed to set component status: {error_text}")
                
                response_data = await response.json()
                print("Response JSON: ", response_data)
                
                return True
        except asyncio.TimeoutError:
            print("Request timed out")
            raise HTTPException(status_code=504, detail="Request timed out")
        except aiohttp.ClientError as e:
            print(f"Connection error: {e}")
            raise HTTPException(status_code=500, detail=f"Connection error: {str(e)}")        
    
        
async def update_user_paid_status(user_id: str, is_paid: bool) -> Dict[str, Any]:
    async with CustomClient(CLERK_SECRET_KEY) as client:
        try:
            # Fetch the current user data
            user: User = await client.users.get(user_id)
            
            # Prepare the update payload
            new_metadata = user.private_metadata.copy()
            new_metadata['isPaidUser'] = is_paid
            
            if is_paid:
                # Remove the 'credits' field for paid users
                new_metadata.pop('credits', None)
            else:
                # For non-paid users, keep existing credits or set to 0
                new_metadata['credits'] = new_metadata.get('credits', 0)
            
            update_payload = {
                "private_metadata": new_metadata
            }
            
            # Update user's private metadata
            async with client.patch(f"users/{user_id}", json=update_payload) as response:
                if response.status == 200:
                    updated_user_data = await response.json()
                    updated_is_paid = updated_user_data.get('private_metadata', {}).get('isPaidUser')
                    if updated_is_paid == is_paid:
                        return {
                            "success": True, 
                            "message": f"User paid status updated successfully to {is_paid}"
                        }
                    else:
                        return {
                            "success": False, 
                            "message": "Failed to update user paid status. Please try again."
                        }
                else:
                    error_data = await response.json()
                    return {
                        "success": False,
                        "message": f"Failed to update user paid status. Status: {response.status}, Error: {error_data}"
                    }
                
        except Exception as e:
            print(f"Error updating user paid status: {str(e)}")
            return {"success": False, "message": f"Error updating user paid status: {str(e)}"}
        

async def call_generate_code_api(user_id, what_and_why, csv_file_path, component_id):
    from modal_api import generate_code_local
    try:
        print("csv_file_path: ", csv_file_path)
        await generate_code_local(user_id, what_and_why, csv_file_path, component_id)
        return {"success": True}    

    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        print(error_message)
        raise HTTPException(status_code=500, detail=error_message)
    

async def update_component_privacy(user_id: str, component_id: str, is_private: bool, clerk_secret_key: str = CLERK_SECRET_KEY) -> Dict[str, Any]:
    if not clerk_secret_key:
        raise ValueError("CLERK_SECRET_KEY is not set")
    
    async with CustomClient(clerk_secret_key) as client:
        print("CLERK_SECRET_KEY: ", clerk_secret_key[:10] + "...")  # Print first 10 characters for debugging
        try:
            # Fetch the current user data
            print("user_id: ", user_id)
            user: User = await client.users.get(user_id)
            
            # Prepare the update payload
            new_metadata = user.private_metadata.copy()
            if 'components' not in new_metadata:
                new_metadata['components'] = {}
            if component_id not in new_metadata['components']:
                new_metadata['components'][component_id] = {}
            new_metadata['components'][component_id]['private'] = is_private
            
            update_payload = {
                "private_metadata": new_metadata
            }
            
            # Update user's private metadata
            async with client.patch(f"users/{user_id}", json=update_payload) as response:
                if response.status == 200:
                    updated_user_data = await response.json()
                    updated_is_private = updated_user_data.get('private_metadata', {}).get('components', {}).get(component_id, {}).get('private')
                    if updated_is_private == is_private:
                        return {
                            "success": True, 
                            "message": f"Component privacy status updated successfully to {is_private}"
                        }
                    else:
                        return {
                            "success": False, 
                            "message": "Failed to update component privacy status. Please try again."
                        }
                else:
                    error_data = await response.json()
                    return {
                        "success": False,
                        "message": f"Failed to update component privacy status. Status: {response.status}, Error: {error_data}"
                    }
                
        except Exception as e:
            print(f"Error updating component privacy status: {str(e)}")
            return {"success": False, "message": f"Error updating component privacy status: {str(e)}"}


async def check_component_public(component_id: str) -> bool:
    user_id = await get_user_id_from_component_id(component_id)
    print("user_id in check_component_public: ", user_id)
    if not user_id:
        return False
    
    async with Client(CLERK_SECRET_KEY) as client:
        user = await client.users.get(user_id)
        return not user.private_metadata.get('components', {}).get(component_id, {}).get('private', True)

async def user_owns_component_or_public(user_id: str, component_id: str) -> bool:
    async with Client(CLERK_SECRET_KEY) as client:
        try:
            user = await client.users.get(user_id)
            
            # Check if the user owns the component based on the component_id format
            component_owner_id = "_".join(component_id.split('_')[:2])
            user_owns_component = user_id == component_owner_id
            
            # Check if the component is public
            components_data = user.private_metadata.get('components', {})
            component_data = components_data.get(component_id, {})
            is_public = not component_data.get('private', True)
            
            return user_owns_component or is_public

        except Exception as e:
            print(f"Error in user_owns_component_or_public: {str(e)}")
            return False


    
async def get_current_user_or_none(x_user_id: Optional[str] = Header(default=None)) -> Optional[User]:
    if not x_user_id:
        return None
    return await get_current_user(x_user_id)



async def get_user_id_from_component_id(component_id: str) -> str:
    parts = component_id.split('_')
    if len(parts) >= 2 and parts[0] == 'user':
        return f"{parts[0]}_{parts[1]}"
    return None


