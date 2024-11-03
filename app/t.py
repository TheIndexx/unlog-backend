from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Header
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
from typing import Dict, Any
from dotenv import load_dotenv
import asyncio
from fastapi import Header, HTTPException
from clerk import Client
from utils import clean_key, clean_value, User
from ssl import SSLCertVerificationError
import boto3
from fastapi.exceptions import RequestValidationError
from fastapi import Request
import aiohttp
load_dotenv('.env.local')
from botocore.exceptions import ClientError
from textwrap import dedent
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential
import asyncio
# from svix.webhooks import Webhook, WebhookVerificationError

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
CLERK_SECRET_KEY = os.getenv('CLERK_SECRET_KEY')

x_user_id = 'user_2mXgLXHGHeOeCoBAyWe92pS6hcA'

async def foo():
  client = Client(CLERK_SECRET_KEY)
  async with client:
    print(client)
    user = await client.users.get(x_user_id)
    print(user)
    print(user.private_metadata)


asyncio.run(foo())