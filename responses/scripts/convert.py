import os
import json
import sys
from datetime import datetime
import requests
import base64
import json

def fetch_authorized_emails_from_github():
    url = "https://api.github.com/repos/theSoberSobber/bluebook/contents/authorized_external_emails.json?ref=emails"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            file_info = response.json()
            content_base64 = file_info.get('content')
            content = base64.b64decode(content_base64).decode('utf-8')
            authorized_emails = json.loads(content)
            inverted_map = {}
            for key in authorized_emails:
                inverted_map[authorized_emails[key]] = key
            return inverted_map
        else:
            print(f"Error: Unable to fetch file. Status code: {response.status_code}")
            return None
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

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
            current_timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
            if latest_timestamp is None or current_timestamp > latest_timestamp:
                latest_timestamp = current_timestamp
                latest_file = file
        
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Skipping file {file} due to error: {e}")
            continue
    return os.path.join(responses_folder, latest_file) if latest_file else None

def convert_to_key_value_pair(data):
    for key in list(data["data"].keys()): # to avoid RTE of changing dict during iteration iterate on list of keys made before hand rather than on dict
        if len(data["data"][key]) == 0:
            del data["data"][key]
            continue
        data["data"][key] = ", ".join(data["data"][key])
        data["data"][key] += ("." if data["data"][key][:-1]=="." else "")
    return data

def convert_to_markdown(latest_file_path):
    
    with open(latest_file_path, 'r') as file:
        data = json.load(file)
    
    data = convert_to_key_value_pair(data)

    email_map = fetch_authorized_emails_from_github()

    markdown_content = f"---\n"
    
    name = data["data"].get("Name", "").strip() or None
    college = data["data"].get("College", "").strip() or None
    company = data["data"].get("Company Appeared For", "").strip() or None
    linkedin = data["data"].get("Linkedin Profile (if interested)", "").strip() or None
    placement_profile = data["data"].get("Placement Profile", "").strip() or None
    email = (
        next((
                e
                for e in [
                    data.get("email", "").strip(),
                    data.get("data", {}).get("Email", "").strip(),
                    email_map.get(data.get("data", {}).get("Email", "").strip(), "").strip()
                ]
                if e.endswith(".ac.in")
            ),
            None
        )
    )
    timestamp = data.get("timestamp", "").strip() or None
    
    if name and company:
        markdown_content += f'title: "{name} - {company}"\n'
        markdown_content += f'summary: Read about my interview experience at {company}\n'
        #markdown_content += f'aliases: ["/{"-".join(name.lower().split(" "))}-{company.lower()}-{college.lower()}"]\n'
        markdown_content += f'tags: ["{company}", "{college}"]\n'
    
    if timestamp:
        markdown_content += f'date: "{timestamp}"\n'
    
    markdown_content += f'series: ["PaperMod"]\n'
    markdown_content += f'weight: 1\n'
    
    if linkedin:
        markdown_content += f'linkedin: "{linkedin}"\n'
    
    if company:
        markdown_content += f'companies: ["{company}"]\n'

    if college:
        markdown_content += f'colleges: ["{college}"]\n'
    
    if placement_profile:
        markdown_content += f'profiles: ["{placement_profile}"]\n'
    
    if name and email:
        markdown_content += f'author: ["{name} - {email}"]\n'
    
    markdown_content += f"---\n"
    markdown_content += f"---\n"


    question_number = 1

    for key in data["data"]:
        if(key.lower()=="email"): continue
        markdown_content += f'{question_number}. ### {key}\n\n'
        markdown_content += f'> '
        markdown_content += (f'{{{{< collapse summary="Expand" >}}}}\n\n{data["data"][key]}\n\n{{{{< /collapse >}}}}\n' 
                                if len(data["data"][key]) > 54
                                else f'{data["data"][key]}\n'
                            )
        markdown_content += f'\n---\n\n'
        question_number+=1
    return markdown_content

def save_as_content_file(file_name, markdown_string):
    with open(file_name, 'w', encoding='utf-8') as file:
        file.write(markdown_string)

responses_folder = "responses"
output_folder = "content/responses/bluebook"

if len(sys.argv) > 1:
    latest_file_path = sys.argv[1]
else:
    latest_file_path = get_latest_response_file(responses_folder=responses_folder)

print(latest_file_path)
if not latest_file_path:
    print("No Valid Files Found in this Commit.")
    exit(1)
markdown_string = convert_to_markdown(latest_file_path)
content_file_path = os.path.join(output_folder, os.path.basename(latest_file_path).replace(".json", ".md"))
save_as_content_file(file_name=content_file_path, markdown_string=markdown_string)
exit(0)