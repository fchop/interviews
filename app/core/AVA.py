import openai
import os
from openai import OpenAI
from dotenv import load_dotenv
import re

load_dotenv()  # This reads from the .env file
AVA_API_KEY = os.getenv("AVA_API_KEY")

client = OpenAI(
    api_key = AVA_API_KEY,
    base_url='https://api.nouswise.ai/v1'
)



def get_llm_response(messages, stream=False):
    MODEL = "standard"
    project_id = "a21953bb-f759-458b-aaad-c41020ebed7b"

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        stream=stream,
        extra_body={'projectId': project_id}, 
        max_completion_tokens=100
    )
    if stream:
        return response  # Caller handles streaming
    
    content = response.choices[0].message.content

    # Remove or replace any unreplaced curly-brace placeholders
    # Option 1: Remove them
    content = re.sub(r"\{[^{}]+\}", "", content)

    # Option 2: (Alternative) Raise an error if found
    # if re.findall(r"\{[^{}]+\}", content):
    #     raise ValueError(f"LLM response contains unreplaced placeholders: {content}")

    return content