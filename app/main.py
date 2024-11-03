import certifi
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json
import os
import time
import uvicorn
from clerk import Client
import logging
from clerk.types import User
from typing import Dict, Any
from dotenv import load_dotenv
from fastapi import HTTPException
from clerk import Client
from utils import User, FetchComponentRequest
from functions import get_current_user, reduce_user_credits, upload_to_s3, read_from_s3, get_user_ui_names, fetch_component_status, set_component_status, call_generate_code_api, update_user_paid_status, update_component_privacy, check_component_public, get_user_id_from_component_id, user_owns_component_or_public, get_current_user_or_none, get_user_id_from_component_id, grant_initial_credits, CustomClient, add_user_credits
import aiohttp
from urllib.parse import urlencode
from fastapi import BackgroundTasks
import boto3
from botocore.exceptions import ClientError
from stripe import StripeClient
import stripe
import traceback
from svix.webhooks import Webhook, WebhookVerificationError
import ssl
print(f"Stripe version: {stripe._version}")

import tempfile
from typing import Optional
from stripe.error import SignatureVerificationError, StripeError

app = FastAPI(debug=True)


logging.basicConfig(level=logging.DEBUG)
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
import pathlib
BASE_DIR = pathlib.Path(__file__).resolve().parent
env_path = BASE_DIR / ".env.local"
load_dotenv(env_path)

#load_dotenv('.env.local')

# Get the value of the ANTHROPIC_API_KEY from environment variables
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
CLERK_SECRET_KEY = os.getenv('CLERK_SECRET_KEY')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ID')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
CLERK_WEBHOOK_SECRET = os.getenv('CLERK_WEBHOOK_SECRET')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
print("ANTHROPIC_API_KEY: ", ANTHROPIC_API_KEY)
print("CLERK_SECRET_KEY: ", CLERK_SECRET_KEY)
print("CLERK_WEBHOOK_SECRET: ", CLERK_WEBHOOK_SECRET)
print("STRIPE_SECRET_KEY: ", STRIPE_SECRET_KEY)

UPLOAD_FOLDER = './uploads'
COMPONENT_FOLDER = './components'
stripe_client = StripeClient(STRIPE_SECRET_KEY)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(COMPONENT_FOLDER, exist_ok=True)


@app.get("/api/user/private-metadata")
async def get_user_private_metadata(current_user: User = Depends(get_current_user)):
    print("in get_user_private_metadata")
    try:
        client = CustomClient(CLERK_SECRET_KEY)
        async with client:
            user = await client.users.get(current_user.id)
            # print("user: ", user)
            return JSONResponse(content={
                "privateMetadata": user.private_metadata,
            }, status_code=200)

    except Exception as e:
        logger.error(f"Error fetching private metadata for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching private metadata")
    

class ReduceCreditsRequest(BaseModel):
    user_id: str
    amount: int = 1

# Example usage in a FastAPI route
@app.post("/reduce-credits")
async def reduce_credits(request: ReduceCreditsRequest):
    print("in reduce_credits")
    print("request: ", request)
    result = await reduce_user_credits(request.user_id, request.amount)
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


def generate_component_id(user_id: str) -> str:
    # Generate a unique identifier (e.g., timestamp or UUID)
    unique_id = str(int(time.time()))  # or use uuid.uuid4()
    return f"{user_id}_GeneratedComponent_{unique_id}"

class StatusRequest(BaseModel):
    component_id: str
    
@app.post("/api/check-component-status")
async def check_component_status(request: StatusRequest, current_user: Optional[User] = Depends(get_current_user_or_none)):
    component_id = request.component_id
    
    s3_client = boto3.client('s3',
        aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['AWS_SECRET_ID']
    )
    
    s3_bucket = os.environ.get('S3_BUCKET_NAME')
    
    # Extract user_id from component_id
    user_id = await get_user_id_from_component_id(component_id)
    
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid component ID")
    
    s3_key_folder = os.path.join(str(user_id), component_id)
    
    files_to_check = [
        f"{component_id}.js",
    ]
    
    try:
        for file in files_to_check:
            s3_key = f"{s3_key_folder}/{file}"
            print(f"Checking S3 key: {s3_key}")
            try:
                s3_client.head_object(Bucket=s3_bucket, Key=s3_key)
                print(f"File {file} found in S3")
            except ClientError as e:
                if e.response['Error']['Code'] == "404":
                    print(f"File {file} not found in S3")
                    return "pending"
                else:
                    print(f"Error checking S3 for file {file}: {str(e)}")
                    raise HTTPException(status_code=500, detail="Error checking S3")
        
        print("All required files found in S3")
        return "completed"
    
    except Exception as e:
        print(f"Error checking S3 for component status: {str(e)}")
        return "error"

class CheckoutSessionRequest(BaseModel):
    priceId: str
    userId: str

def parse_signature_header(header):
    pairs = header.split(',')
    parsed = {}
    for pair in pairs:
        key, value = pair.split('=')
        parsed[key] = value
    return parsed['t'], [parsed['v1']] if 'v1' in parsed else []


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
        async with CustomClient(CLERK_SECRET_KEY) as client:
            user = await client.users.get(request.userId)
        
        session = stripe_client.checkout.sessions.create(
        params={
                "mode": "subscription",
                "line_items": [{
                    "price": request.priceId,
                    "quantity": 1,
                }],
                "success_url": f"{os.getenv('NEXT_PUBLIC_SITE_URL')}",
                "cancel_url": os.getenv('NEXT_PUBLIC_SITE_URL'),
                "client_reference_id": request.userId,
            }
        )

        return {"checkoutUrl": session.url}
    except Exception as e:
        print(f"Error creating checkout session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred while creating the checkout session: {str(e)}")


async def handle_successful_payment(session):
    user_id = session.get('client_reference_id')
    if not user_id:
        print("No user_id found in session")
        return

    try:
        client = CustomClient(CLERK_SECRET_KEY)
        async with client:
            user = await client.users.get(user_id)
            
            # Get the customer ID from the session
            customer_id = session.get('customer')
            
            # Create new metadata by copying existing metadata and updating values
            new_metadata = user.private_metadata.copy()
            new_metadata['stripeCustomerId'] = customer_id
            new_metadata['isPaidUser'] = True
            
            # Update user's private metadata using patch
            async with client.patch(f"users/{user_id}", json={"private_metadata": new_metadata}) as response:
                if response.status == 200:
                    print(f"User {user_id} successfully upgraded to paid status with Stripe customer ID: {customer_id}")
                else:
                    print(f"Failed to update user metadata. Status: {response.status}")
    except Exception as e:
        print(f"Error updating user {user_id} metadata: {str(e)}")
        
    
@app.get("/api/list-user-uis")
async def list_user_uis(current_user: User = Depends(get_current_user)):
    print("\n--- Starting /api/list-user-uis ---")
    user_id = str(current_user.id)
    print(f"Listing UIs for user: {user_id}")

    ui_info = get_user_ui_names(user_id)

    print("--- Finishing /api/list-user-uis ---")
    return JSONResponse(content={
        "message": "User UIs listed successfully",
        "ui_info": ui_info
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



@app.get("/api/get-privacy")
async def get_privacy(component_id: str, current_user: User = Depends(get_current_user)):
    if not component_id:
        raise HTTPException(status_code=400, detail="Component ID is required")
    
    client = CustomClient(CLERK_SECRET_KEY)
    async with client:
        user: User = await client.users.get(current_user.id)
        is_private = user.private_metadata.get('components', {}).get(component_id, {}).get('private', True)
        
        return JSONResponse(content={"is_private": is_private}, status_code=200)



@app.post("/api/toggle-privacy")
async def toggle_privacy(request: Request, current_user: User = Depends(get_current_user)):
    try:
        data = await request.json()
        component_id = data.get('component_id')
        
        if not component_id:
            raise HTTPException(status_code=400, detail="Component ID is required")
        
        # Fetch the current privacy status
        client = CustomClient(CLERK_SECRET_KEY)
        async with client:
            user: User = await client.users.get(current_user.id)
            print("user: ", user)
            print("user.private_metadata: ", user.private_metadata)
            current_privacy = user.private_metadata.get('components', {}).get(component_id, {}).get('private', True)
            new_privacy = not current_privacy
            print("new_privacy: ", new_privacy)
            # Update the privacy status
            result = await update_component_privacy(user.id, component_id, new_privacy, CLERK_SECRET_KEY)
            
            if result['success']:
                return JSONResponse(content={"message": f"Privacy toggled to {new_privacy}", "is_private": new_privacy}, status_code=200)
            else:
                raise HTTPException(status_code=500, detail=result['message'])
    except Exception as e:
        logger.error(f"Error in toggle_privacy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    

class CancelSubscriptionRequest(BaseModel):
    user_id: str

@app.post("/api/cancel-subscription")
async def cancel_subscription(
    request: CancelSubscriptionRequest,
    current_user: User = Depends(get_current_user)
):
    if current_user.id != request.user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    try:
        async with CustomClient(CLERK_SECRET_KEY) as client:
            user = await client.users.get(request.user_id)
        
            print(f"Stripe customer ID: {user.private_metadata.get('stripeCustomerId')}")
                
            subscriptions = stripe_client.subscriptions.list(
                params={
                    "customer": user.private_metadata.get('stripeCustomerId'),
                    "status": "active",
                    "limit": 1
                }
            )
            print(f"Subscriptions found: {subscriptions.data}")

            if not subscriptions.data:
                raise HTTPException(status_code=404, detail="No active subscription found")
                
            subscription = stripe_client.subscriptions.cancel(subscriptions.data[0].id)
            print(f"Subscription cancelled: {subscription.status}")
            
            # Updated metadata handling to match handle_successful_payment pattern
            new_metadata = user.private_metadata.copy()
            new_metadata['isPaidUser'] = False
            
            async with client.patch(f"users/{request.user_id}", json={"private_metadata": new_metadata}) as response:
                if response.status == 200:
                    print(f"User {request.user_id} successfully downgraded from paid status")
                else:
                    print(f"Failed to update user metadata. Status: {response.status}")
            
            return JSONResponse(content={
                "message": "Subscription cancelled successfully",
                "status": subscription.status
            }, status_code=200)
        
    except StripeError as e:
        print(f"Stripe error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error cancelling subscription: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/stripe-webhook")
async def stripe_webhook(request: Request):
    print("\n--- Webhook Debug Start ---")
    
    try:
        # 1. Print all headers
        print("All Headers:")
        for key, value in request.headers.items():
            print(f"{key}: {value}")
        
        # 2. Get the payload and signature
        payload = await request.body()
        # sig_header = request.headers.get("Stripe-Signature")
        sig_header = request.headers.get('stripe-signature')
        webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        
        print(f"\nPayload (first 100 chars): {payload}")
        print(f"Signature header: {sig_header}")
        print(f"Webhook secret first 5 chars: {webhook_secret[:5] if webhook_secret else 'None'}")
        
        if not sig_header:
            raise ValueError("No Stripe-Signature header found")
        
        if not webhook_secret:
            raise ValueError("Webhook secret is not set")
        
        # 3. Construct and verify the event
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret,
                # tolerance=300  # Increase tolerance to 5 minutes
            )
            print(f"\nEvent constructed successfully. Type: {event['type']}")
        except ValueError as e:
            print(f"ValueError in construct_event: {str(e)}")
            raise
        except SignatureVerificationError as e:
            print(f"SignatureVerificationError: {str(e)}")
            raise
        
        # Process the event...
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            user_id = session.get('client_reference_id')

            # Get subscription details
            subscription_id = session.get('subscription')
            if subscription_id:
                subscription = stripe_client.subscriptions.retrieve(subscription_id)
                price_id = subscription.plan.id
                
                # Define credit amounts for each plan
                PLAN_CREDITS = {
                    'price_1QFshdGZgEaeKhVdSK6vvaBP': 100,    # Basic plan - dummy ID
                    'price_1QFsi4GZgEaeKhVdwFvXVhPL': 250,      # Pro plan - dummy ID
                    'price_1QFsikGZgEaeKhVd9rvtcbMA': 1000  # Enterprise plan - dummy ID
                }
                
                # Get credits amount based on the price ID
                credits_to_add = PLAN_CREDITS.get(price_id)
            
                if user_id and credits_to_add:
                    print(f"Processing completed checkout for user: {user_id}")
                    await add_user_credits(user_id, credits_to_add)
                    await handle_successful_payment(session)
                    # Implement your user status update logic here
                    # await update_user_paid_status(user_id, True)
                else:
                    print("No user_id found in the session")

        return {"status": "success"}

    except ValueError as e:
        print(f"\nValueError: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except SignatureVerificationError as e:
        print(f"\nSignatureVerificationError: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid signature: {str(e)}")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    finally:
        print("--- Webhook Debug End ---\n")

@app.post("/api/clerk-usercreated-webhook")
async def clerk_usercreated_webhook(request: Request):
    logger.info("Webhook endpoint called")
    try:
        # Get the raw payload
        logger.debug("Attempting to read raw payload")
        raw_payload = await request.body()
        logger.debug(f"Raw payload: {raw_payload}")
        
        # Get the headers
        logger.debug("Extracting headers")
        svix_id = request.headers.get("svix-id")
        svix_timestamp = request.headers.get("svix-timestamp")
        svix_signature = request.headers.get("svix-signature")
        logger.debug(f"Headers: svix-id={svix_id}, svix-timestamp={svix_timestamp}, svix-signature={svix_signature}")

        # Verify the webhook
        logger.info("Verifying webhook")
        wh = Webhook(CLERK_WEBHOOK_SECRET)
        try:
            payload = wh.verify(raw_payload, {
                "svix-id": svix_id,
                "svix-timestamp": svix_timestamp,
                "svix-signature": svix_signature
            })
            logger.debug(f"Verified payload: {payload}")
        except WebhookVerificationError as e:
            logger.error(f"Webhook verification failed: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Webhook verification failed: {str(e)}")

        # Check if this is a user.created event
        event_type = payload.get('type')
        logger.info(f"Event type: {event_type}")
        if event_type != 'user.created':
            logger.info("Not a user.created event, no action taken")
            return {"message": "Not a user.created event, no action taken"}

        # Extract the user ID from the payload
        user_id = payload.get('data', {}).get('id')
        logger.info(f"Extracted user ID: {user_id}")
        if not user_id:
            logger.error("User ID not found in payload")
            raise HTTPException(status_code=400, detail="User ID not found in payload")
        
        # Extract user information from the payload
        user_data = payload.get('data', {})
        user_id = user_data.get('id')
        email_addresses = user_data.get('email_addresses', [])
        email = email_addresses[0].get('email_address') if email_addresses else None
        username = user_data.get('username')
        logger.info(f"User information: ID={user_id}, email={email}, username={username}")

        # Create user on backend
        backend_url = "https://a6mr5neyefbjju7kqtgr4gj4wy0xvywo.lambda-url.us-east-2.on.aws/"
        create_user_payload = {
            "user_id": user_id,
            "email": email,
            "username": username
        }
        
        # Create SSL context that verifies certificates
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        async with aiohttp.ClientSession() as session:
            async with session.post(backend_url, json=create_user_payload, ssl=ssl_context) as response:
                if response.status != 200:
                    logger.error(f"Failed to create user on backend: {await response.text()}")
                    raise HTTPException(status_code=500, detail="Failed to create user on backend")
                logger.info("User created successfully on backend")

        # Grant initial credits to the new user
        logger.info(f"Granting initial credits to user {user_id}")
        result = await grant_initial_credits(user_id)
        
        if result["success"]:
            logger.info(f"Credits granted successfully: {result['message']}")
            return {"message": result["message"]}
        else:
            logger.error(f"Failed to grant credits: {result['message']}")
            raise HTTPException(status_code=400, detail=result["message"])

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON payload: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {str(e)}")
    except Exception as e:
        logger.exception("Unexpected error occurred")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
    # uvicorn.run(app, host="127.0.0.1", port=8000)