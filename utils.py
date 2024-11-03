from pydantic import BaseModel
import re
from typing import List, Dict, Any, Union


def clean_key(key: str) -> str:
    key = key.lstrip('\ufeff')
    key = re.sub(r'[^\w]', '_', key)
    return key.lower()

def clean_value(value: str) -> Any:
    value = value.strip()
    if value == '':
        return None
    if value.lower() == 'true':
        return True
    if value.lower() == 'false':
        return False
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


class User(BaseModel):
    id: str
    first_name: str
    last_name: str
    email_address: str
    credits: int
    is_paid_user: bool


class VisualizeRequest(BaseModel):
    what_and_why: str
    input_file: str
    api_key: str
    
    
    
class FetchComponentRequest(BaseModel):
    component_id: str