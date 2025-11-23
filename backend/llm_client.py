# backend/llm_client.py

import os
import json
import re
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

# Load Groq API Key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize Groq LLM
llm = ChatGroq(
    model="openai/gpt-oss-120b",   
    temperature=0.2,
)

def extract_json(text: str):
    """
    Extracts the first valid JSON object or array from LLM output.
    Returns a Python dict/list if valid, otherwise a safe error dict.
    """
    if not text:
        return {"error": "Empty LLM response"}

    # Find ANY JSON object or array in the text
    match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    
    if match:
        json_str = match.group(0).strip()
        try:
            return json.loads(json_str)
        except Exception as e:
            return {
                "error": "Invalid JSON structure returned by LLM",
                "raw_extract": json_str,
                "details": str(e)
            }

    return {
        "error": "No JSON found in LLM output",
        "raw_output": text
    }


def call_llm(prompt: str):
    """
    Calls the Groq LLM and returns a Python dict.
    This protects the UI from JSON parse errors.
    """

    try:
        # Invoke Groq model
        response = llm.invoke(prompt)
        raw_text = response.content.strip()

        # Extract JSON safely
        return extract_json(raw_text)

    except Exception as e:
        return {
            "error": "LLM call failed",
            "details": str(e)
        }

val = call_llm('who are you')
print(val)