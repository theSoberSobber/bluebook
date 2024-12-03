import os
import json

def get_latest_response_file(responses_folder):
    files = os.listdir(responses_folder)
    
    latest_file = None
    highest_response_number = -1
    
    for file in files:
        if not file.startswith("response_") or not file.endswith(".json"): continue
        response_number = int(file.split("_")[1])
        if response_number > highest_response_number:
            highest_response_number = response_number
            latest_file = file
    
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

    markdown_content = f"---\n"
    markdown_content += f'title: "{data["data"]["Name"]} - {data["data"]["Company Appeared For"]}"\n'
    markdown_content += f'summary: Read about my interview experience at {data["data"]["Company Appeared For"]}\n'
    markdown_content += f'date: "{data["timestamp"]}"\n'
    markdown_content += f'series: ["PaperMod"]\n'
    markdown_content += f'weight: 1\n'
    markdown_content += f'aliases: ["/{"-".join(data["data"]["Name"].lower().split(" "))}-{data["data"]["Company Appeared For"].lower()}"]\n'
    markdown_content += f'tags: ["{data["data"]["Company Appeared For"]}"]\n'
    markdown_content += f'linkedin: ["{data["data"]["Linkedin Profile (if interested)"]}"]\n'
    markdown_content += f'companies: ["{data["data"]["Company Appeared For"]}"]\n'
    markdown_content += f'profiles: ["{data["data"]["Placement Profile"]}"]\n'
    markdown_content += f'author: ["{data["data"]["Name"]} - {data["email"]}"]\n'
    markdown_content += f"---\n"
    markdown_content += f"---\n"

    question_number = 1

    for key in data["data"]:
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
latest_file_path = get_latest_response_file(responses_folder=responses_folder)
print(latest_file_path)
if not latest_file_path:
    print("No Valid Files Found in this Commit.")
    exit(1)
markdown_string = convert_to_markdown(latest_file_path)
content_file_path = os.path.join(output_folder, os.path.basename(latest_file_path).replace(".json", ".md"))
save_as_content_file(file_name=content_file_path, markdown_string=markdown_string)
exit(0)