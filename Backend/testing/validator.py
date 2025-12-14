from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAI(
    base_url="https://openrouter.ai/api/v1", 
    api_key=os.environ.get("API")
)

model_name = "meta-llama/llama-4-maverick:free"

sys_prompt = (
    "You are a validator for a product retriever LLM. You will be given a prompt from the user and the output of the LLM. Your job is to:" \
    "1/ Validate if the output return by the LLM is correct by comparing it with the user query. Retrun ONLY 'yes' or 'no'." \
    "2/ "
)

response = client.chat.completions.create(
    model=model_name,
    messages=[
        {
            'role': 'system',
            'content': sys_prompt
        },
        {
            'role': 'user',
            'content': None
        }
    ],
    response_format={
        "type": 'json_schema',
        "json_schema": {
            "name": "validator_response",
            "schema": {
                "type": "object",
                "properties": {
                    "is_correct": {
                        "type": "boolean",
                        "description": "Whether the LLM output matches the user query."
                    },
                    "reason": {
                        "type": "string",
                        "description": "Explanation for the validation result."
                    }
                },
                "required": ["is_correct", "reason"],
                "additionalProperties": False
            }
        }
    }
)