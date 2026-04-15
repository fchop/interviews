import json


def clean_interview_output(session_id, folder_path="C:/Users/edward_b/github/interviews/interviews/app/data"):
    json_path = f"{folder_path}/{session_id}.json"
    txt_path = f"{folder_path}/{session_id}_clean.txt"

    # Load the JSON data
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    conversation = []
    for item in data:
        if item["type"] == "question":
            speaker = "Interviewer"
        elif item["type"] == "answer":
            speaker = "Interviewee"
        else:
            continue

        conversation.append(f"{speaker}: {item['content'].strip()}")

    # Save cleaned output
    with open(txt_path, "w", encoding="utf-8") as out_file:
        for line in conversation:
            out_file.write(line + "\n\n")
