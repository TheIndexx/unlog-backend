
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from functions import read_from_s3
import csv
import json
import requests
import os
import time
from typing import List, Dict, Any, Union
import chardet
from textwrap import dedent
from io import StringIO, BytesIO
import pandas as pd
import numpy as np
import random
import uvicorn
import uuid
import subprocess
from clerk import Client
import logging
import math
from datetime import datetime
app = FastAPI(debug=True)
import asyncio
from clerk.types import UpdateUserRequest, User
from typing import Dict, Any
from dotenv import load_dotenv
import re
import io
from collections import Counter
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


import csv
import io
import json
import logging
import pandas as pd
import numpy as np
import re
from datetime import datetime
from typing import List, Dict, Any, Union
from collections import Counter
import dateutil.parser

import chardet
import csv
import io
import json
import logging
import pandas as pd
import numpy as np
import re
from datetime import datetime
from typing import List, Dict, Any, Union
from collections import Counter
import dateutil.parser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def csv_to_json(bucket_name: str, s3_key_folder: str, s3_key: str, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, max_file_size_mb: int = 1000) -> List[Dict[str, Any]]:
    file_content = read_from_s3(bucket_name, s3_key_folder, s3_key, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    
    if file_content is None:
        raise ValueError(f"Failed to read file from S3: {s3_key_folder}/{s3_key}")

    file_size_mb = len(file_content.encode('utf-8')) / (1024 * 1024)
    if file_size_mb > max_file_size_mb:
        error_msg = f"File size ({file_size_mb:.2f} MB) exceeds the maximum allowed size of {max_file_size_mb} MB."
        logger.error(error_msg)
        raise ValueError(error_msg)

    result = chardet.detect(file_content.encode())
    encodings_to_try = [result['encoding'], 'utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
    
    for encoding in encodings_to_try:
        try:
            csv_file = io.StringIO(file_content)
            df = pd.read_csv(csv_file, encoding=encoding, low_memory=False)
            json_data = df.to_dict(orient='records')
            
            # if json_data:
            #     json_data = process_data(json_data)
            
            return json_data
        except Exception as e:
            logger.warning(f"Failed to process with {encoding}: {str(e)}")
    
    
    logger.error("Failed to process the file with all attempted encodings.")
    raise ValueError("Unable to process the CSV file with any of the attempted encodings.")



def process_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    data = [clean_row(row) for row in data]
    data = standardize_data_types(data)
    data = handle_missing_values(data)
    data = normalize_strings(data)
    data = handle_currency(data)
    data = handle_nested_structures(data)
    return data

def clean_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {clean_key(key): clean_value(value) for key, value in row.items()}

def clean_key(key: str) -> str:
    if key is None:
        return 'unknown'
    key = str(key).lstrip('\ufeff')
    key = re.sub(r'[^\w]', '_', key)
    return to_camel_case(key)

def to_camel_case(snake_str: str) -> str:
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

def is_valid_number_with_commas(value: str) -> bool:
    # Check if the value matches the pattern for a number with commas correctly placed
    number_pattern = re.compile(r'^-?\d{1,3}(?:,\d{3})*$')
    return bool(number_pattern.match(value))

def clean_value(value: Any) -> Any:
    if isinstance(value, str) and is_valid_number_with_commas(value):
        return int(value.replace(',', ''))
    return value


def standardize_data_types(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not data:
        return data

    def is_float(value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    column_types = {}
    for column in data[0].keys():
        # print("column", column)
        non_null_values = [row[column] for row in data if row[column] is not None]
        
        if not non_null_values:
            column_types[column] = str
        elif all(isinstance(v, bool) for v in non_null_values):
            column_types[column] = bool
        elif all(isinstance(v, int) for v in non_null_values):
            column_types[column] = int
        else:
            float_values = [float(v) for v in non_null_values if isinstance(v, (int, float)) or (isinstance(v, str) and is_float(v))]
            float_count = len(float_values)
            total_count = len(non_null_values)

            if float_count / total_count > 0.90:
                column_types[column] = float
                avg_value = sum(float_values) / float_count
                # Replace non-float entries with the average value
                for row in data:
                    if row[column] is not None and not (isinstance(row[column], (int, float)) or (isinstance(row[column], str) and is_float(row[column]))):
                        row[column] = avg_value
            else:
                column_types[column] = str


    standardized_data = []
    for row in data:
        standardized_row = {}
        for column, value in row.items():
            try:
                if value is None:
                    standardized_row[column] = None
                elif column_types[column] == bool:
                    standardized_row[column] = bool(value)
                elif column_types[column] == int:
                    standardized_row[column] = int(float(value)) if value is not None else None
                elif column_types[column] == float:
                    standardized_row[column] = float(value) if value is not None else None
                else:
                    standardized_row[column] = str(value) if value is not None else None
            except ValueError:
                logger.warning(f"Could not convert value '{value}' to {column_types[column]} for column '{column}'. Keeping as original type.")
                standardized_row[column] = value
        # print("column 2: ", column)
        # print("standardized_row: ", standardized_row['UserID'])
        standardized_data.append(standardized_row)
    return standardized_data

def handle_missing_values(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Handle missing values in the dataset, replacing both None and NaN with median for numeric columns,
    'nan' strings with 'Not Available' for non-numeric columns, and use a special missing link for link columns.
    
    :param data: List of dictionaries representing the data
    :return: List of dictionaries with missing values handled
    """
    if not data:
        return data

    # Convert list of dicts to pandas DataFrame for easier handling
    df = pd.DataFrame(data)

    # Identify numeric columns
    numeric_columns = df.select_dtypes(include=[np.number]).columns

    # Function to check if a column contains links
    def is_link_column(column):
        non_null_values = df[column].dropna()
        if len(non_null_values) == 0:
            return False
        # Check if more than 50% of non-null values are links
        return non_null_values.str.contains(r'^(?:https?://|www\.)', case=False, na=False).mean() > 0.5

    for column in df.columns:
        if column in numeric_columns:
            # For numeric columns, calculate median ignoring NaN values
            median_value = df[column].median()
            # Replace both None and NaN with median
            df[column] = df[column].fillna(median_value)
        elif is_link_column(column):
            # For link columns, replace missing values with a special missing link
            df[column] = df[column].replace("nan", np.nan).fillna('https://www.missingvalue.com')

        else:
            # For other non-numeric columns, replace 'nan' strings and NaN values with 'Not Available'
            df[column] = df[column].replace({'nan': 'Not Available', np.nan: 'Not Available'})

    # Convert back to list of dictionaries
    return df.to_dict('records')

def normalize_strings(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

    return data



def handle_nested_structures(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for row in data:
        for column, value in row.items():
            if isinstance(value, str):
                try:
                    parsed_value = json.loads(value)
                    if isinstance(parsed_value, (dict, list)):
                        row[column] = parsed_value
                except json.JSONDecodeError:
                    pass
    return data


def is_currency(value: str) -> bool:
    # Define a stricter currency pattern to match only valid currency formats
    currency_pattern = re.compile(r'^[^\d\s]*\s*-?\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?\s*[A-Z]{3}?$')
    match = currency_pattern.match(value)
    return bool(match)

def is_date(value: str) -> bool:
    # Comprehensive list of date patterns
    date_patterns = [
        re.compile(r'^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$'),  # DD/MM/YYYY, MM/DD/YYYY, YYYY/MM/DD
        re.compile(r'^\d{4}[-/]\d{1,2}[-/]\d{1,2}$'),  # YYYY-MM-DD
        re.compile(r'^[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{2,4}$'),  # Month DD, YYYY
        re.compile(r'^\d{1,2}\s+[A-Za-z]{3,9},?\s+\d{2,4}$'),  # DD Month YYYY
        re.compile(r'^[A-Za-z]{3,9}\s+\d{4}$'),  # Month YYYY
        re.compile(r'^\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]{3,9}\s+\d{2,4}$'),  # 1st Jan 2024
        re.compile(r'^\d{1,2}[-/][A-Za-z]{3}[-/]\d{2,4}$'),  # DD-MMM-YYYY
        re.compile(r'^[A-Za-z]{3}[-/]\d{1,2}[-/]\d{2,4}$'),  # MMM-DD-YYYY
        re.compile(r'^\d{4}$'),  # YYYY (for year-only values)
    ]
    for pattern in date_patterns:
        if pattern.match(value):
            return True
    return False

def process_currency_value(value: str) -> str:
    currency_pattern = re.compile(r'^(?P<symbol>[^\d\s]*)\s*(?P<amount>-?\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)\s*(?P<code>[A-Z]{3})?$')
    match = currency_pattern.match(value)
    if match:
        amount_str = match.group('amount').replace(',', '')
        if amount_str.replace('.', '', 1).isdigit():
            amount = float(amount_str)
            symbol = match.group('symbol') or ''
            code = match.group('code') or ''
            return f"{symbol}{amount} {code}".strip()
    return value  # Return the original value if it's not a valid currency

def handle_currency(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for row in data:
        for column, value in row.items():
            if isinstance(value, str):
                value = value.strip()
                if is_date(value):
                    # print(f"Skipping date value: {value}")
                    continue
                if is_currency(value):
                    row[column] = process_currency_value(value)
                # else:
                    # print(f"Value '{value}' is not a currency")
            # else:
                # print(f"Skipping non-string value: {value}")
    return data


def json_to_csv(json_data: List[Dict[str, Any]]) -> str:
    if not json_data:
        logger.warning("No data provided to convert.")
        return ""
    
    # Flatten nested structures
    flat_data = []
    for row in json_data:
        flat_row = {}
        for key, value in row.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    flat_row[f"{key}_{sub_key}"] = sub_value
            elif isinstance(value, list):
                flat_row[key] = json.dumps(value)
            else:
                flat_row[key] = value
        flat_data.append(flat_row)

    # Get the headers from the keys of the first dictionary in the list
    headers = list(set().union(*(d.keys() for d in flat_data)))

    output = io.StringIO()
    try:
        csv_writer = csv.DictWriter(output, fieldnames=headers, extrasaction='ignore')
        csv_writer.writeheader()
        for row in flat_data:
            csv_writer.writerow(row)
        
        csv_content = output.getvalue()
    except Exception as e:
        logger.error(f"Error in json_to_csv: {str(e)}")
        return ""
    finally:
        output.close()
    
    return csv_content


def sample_df_with_char_limit(df, char_limit=1000):
    df['char_count'] = df.astype(str).sum(axis=1).str.len()
    df_sorted = df.sort_values('char_count')
    
    total_chars = 0
    rows_to_include = 0
    
    for _, row in df_sorted.iterrows():
        if total_chars + row['char_count'] <= char_limit:
            total_chars += row['char_count']
            rows_to_include += 1
        else:
            break
    
    sample_df = df_sorted.head(rows_to_include)
    sample_df = sample_df.drop('char_count', axis=1)
    data_sample_str_csv = sample_df.to_string(index=False)
    
    return sample_df, data_sample_str_csv
