import os
import json
import sys
from datetime import datetime
import requests
import base64

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

def get_all_response_files(responses_folder):
    files = []
    for file in os.listdir(responses_folder):
        if file.startswith("response_") and file.endswith(".json"):
            files.append(os.path.join(responses_folder, file))
    return files

def get_latest_response_file(responses_folder):
    files = get_all_response_files(responses_folder)
    latest_file = None
    latest_timestamp = None

    for file in files:
        try:
            with open(file, 'r') as f:
                data = json.load(f)
            current_timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
            if latest_timestamp is None or current_timestamp > latest_timestamp:
                latest_timestamp = current_timestamp
                latest_file = file
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Skipping file {file} due to error: {e}")
            continue

    return latest_file

def convert_to_key_value_pair(data):
    for key in list(data["data"].keys()):
        if len(data["data"][key]) == 0:
            del data["data"][key]
            continue
        data["data"][key] = ", ".join(data["data"][key])
        data["data"][key] += ("." if data["data"][key][:-1] == "." else "")
    return data

def convert_to_markdown(latest_file_path):
    with open(latest_file_path, 'r') as file:
        data = json.load(file)

    data = convert_to_key_value_pair(data)
    # email_map = fetch_authorized_emails_from_github()
    email_map = {}

    markdown_content = f"---\n"

    name = data["data"].get("Name", "").strip() or None
    if name is not None:
        name = " ".join(word[0].upper() + word[1:] for word in name.split(' '))
    college = data["data"].get("College", "").strip() or None
    if college is not None:
        college = college.replace(",", "") # some were using commas in college names, those don't translate in URLs, leading to overcounting
    company = data["data"].get("Company Appeared For", "").strip() or None
    if company:
        company = company.replace(".", "") # de shaw normalization
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
        markdown_content += f'tags: ["{company}", "{college}"]\n'

    if timestamp:
        markdown_content += f'date: "{timestamp}"\n'

    markdown_content += f'series: ["PaperMod"]\n'
    markdown_content += f'aliases: ["/responses/bluebook/{os.path.basename(latest_file_path).replace(".json", "")}", "/responses/bluebook/{get_file_name(latest_file_path)}"]\n'
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
        if key.lower() == "email": continue
        displayKey = key.replace("(if interested)", "").strip() # remove if interested part from being displayed in optional questions
        markdown_content += f'{question_number}. ### {displayKey}\n\n'
        markdown_content += f'> '
        markdown_content += (f'{{{{< collapse summary="Expand" >}}}}\n\n{data["data"][key]}\n\n{{{{< /collapse >}}}}\n' 
                                if len(data["data"][key]) > 54
                                else f'{data["data"][key]}\n'
                            )
        markdown_content += f'\n---\n\n'
        question_number += 1
    return markdown_content

def get_file_name(latest_file_path):
    with open(latest_file_path, 'r') as file:
        data = json.load(file)

    data = convert_to_key_value_pair(data)

    name = data["data"].get("Name", "").strip() or None
    # college = data["data"].get("College", "").strip() or None
    company = data["data"].get("Company Appeared For", "").strip() or None
    return f"{name.lower().replace(' ', '-')}-{company.lower().replace(' ', '-')}"

def save_as_content_file(file_name, markdown_string):
    with open(file_name, 'w', encoding='utf-8') as file:
        file.write(markdown_string)

responses_folder = "responses"
output_folder = "content/responses"

if len(sys.argv) > 1 and sys.argv[1] == "--all":
    files_to_process = get_all_response_files(responses_folder)
else:
    latest_file_path = get_latest_response_file(responses_folder=responses_folder)
    files_to_process = [latest_file_path] if latest_file_path else []

if not files_to_process:
    print("No Valid Files Found in this Commit.")
    exit(1)

for file_path in files_to_process:
    markdown_string = convert_to_markdown(file_path)
    file_name = get_file_name(file_path)
    content_file_path = os.path.join(output_folder, file_name + ".md")
    save_as_content_file(file_name=content_file_path, markdown_string=markdown_string)
    print(f"Processed: {file_path} -> {content_file_path}")

exit(0)