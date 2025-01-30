import os
import json
import sys
from datetime import datetime
import requests
import base64

responses_folder = "responses"

def get_latest_response_file(responses_folder):
    files = os.listdir(responses_folder)
    latest_file = None
    latest_timestamp = None
    
    for file in files:
        if not file.startswith("response_") or not file.endswith(".json"): 
            continue
        
        try:
            full_path = os.path.join(responses_folder, file)
            with open(full_path, 'r') as f:
                data = json.load(f)
            
            if 'timestamp' not in data:
                continue
            
            current_timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
            if latest_timestamp is None or current_timestamp > latest_timestamp:
                latest_timestamp = current_timestamp
                latest_file = file
        
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Skipping file {file} due to error: {e}")
            continue
    
    return os.path.join(responses_folder, latest_file) if latest_file else None

def fetch_authorized_emails_from_github():
    url = "https://api.github.com/repos/theSoberSobber/bluebook/contents/authorized_external_emails.json?ref=emails"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            file_info = response.json()
            content_base64 = file_info.get('content')
            
            if content_base64 is None:
                print("Error: No content found in response.")
                return None
            
            content = base64.b64decode(content_base64).decode('utf-8')
            authorized_emails = json.loads(content)
            return {v: k for k, v in authorized_emails.items()}
        else:
            print(f"Error: Unable to fetch file. Status code: {response.status_code}")
            return None
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

file_path = get_latest_response_file(responses_folder)

if file_path is None:
    print("No valid response file found.")
    sys.exit(1)

try:
    with open(file_path, 'r') as f:
        pr_data = json.load(f)
except (json.JSONDecodeError, FileNotFoundError) as e:
    print(f"Error reading response file: {e}")
    sys.exit(1)

validEmail = 0
email_map = fetch_authorized_emails_from_github() or {}

email_key = pr_data.get("email", "").strip()
email_list = pr_data.get("data", {}).get("Email", [])

if email_list and isinstance(email_list, list):
    email_value = email_list[0].strip()
else:
    email_value = ""

if email_key.endswith(".ac.in") or email_value.endswith(".ac.in"):
    validEmail |= 1

if email_map.get(email_value, "").strip().endswith(".ac.in"):
    validEmail |= 1

print(validEmail)