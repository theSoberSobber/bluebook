import json
import os

responses_folder = "responses"

from datetime import datetime

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

file_path = get_latest_response_file(responses_folder=responses_folder)

with open(file_path, 'r') as f:
    pr_data = json.load(f)

qa_data = pr_data["data"]

prompt = "You are given a bunch of questions and answers pertaining to a document that contains interview transcripts for candidates that have been selected into companies, please flag the document into suitable for publishing on a public facing site or not. Provide a one liner reason flagging the parts that are problematic. We are defining problematic here as profanities/slurs etc. The text can be flagged if the content doesn't seem relevant to our interview experience publishing site too (basically we are trying to avoid spam and hateful speech). The text can be multilingual. You must output in this format: <Yes/No>. <Reasoning Highlighting the Problematic Parts if No>. Please note that we are not expected an evaluation for each question, just one singular evaluation for the whole thing in the given input format.\n\n"

for question, answer in qa_data.items():
    if not len(answer): continue
    prompt += f"Question: {question}\nAnswer: {', '.join(answer)}\n\n"

print(prompt)