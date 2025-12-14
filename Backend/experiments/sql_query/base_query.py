import os
from supabase import create_client
from dotenv import load_dotenv
import json
from typing import *
from openai import OpenAI

load_dotenv()

url = os.environ.get("SUPABASE_URL")
database_key = os.environ.get("SUPABASE_KEY")
openai_key = os.environ.get('OPENAI_KEY')

supabase = create_client(url, database_key)

compare_budget_to = 'final_price'

sys_prompt = '''You are a shop item information extraction assistant. Your job is to extract information from the user's text and return it in a specific JSON format with EXACTLY these keys:

1. "objective": The main item the user is looking for (e.g., "computer", "TV", "game").

2. "budget": The user's budget constraint formatted as "{relational_operator}{price}{currency}".
   Example: "<4000$" for less than 4000 dollars. Return null if not mentioned.

3. "brand": A LIST of brands mentioned by the user, even if there's only one brand.
   Example: ["Samsung", "LG"]. Return null if no brands mentioned.

4. "preferences": A DICTIONARY with exactly two keys - "yes" and "no":
   - "yes": LIST of features/attributes the user wants
   - "no": LIST of features/attributes the user doesn't want
   Example: {"yes": ["long battery life", "good webcam"], "no": ["DELL", "MSI"]}
   Return empty lists if nothing is specified: {"yes": [], "no": []}

You must use EXACTLY these field names: "objective", "budget", "brand", and "preferences".
'''
prompt = 'I want an AC power cord from OMNIHIL'

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=openai_key,
)

response = client.chat.completions.create(
  model="openai/gpt-oss-20b:free",
  messages=[
    {
      "role": "system",
      "content": sys_prompt
    },
    {
      "role": "user",
      "content": prompt
    }
  ],
  response_format={"type": "json_object"}
)

json_response = response.choices[0].message.content
data = json.loads(json_response)

def generate_product_search_query(
        objective: str,
        brand: list,
        budget: str,
        like: list,
        dislike: list
):
    query = f"""
    SELECT * FROM data
    WHERE
    """
    
    # Objective/Title matching
    if objective:
        query += f" title ILIKE '%{objective}%'"
    
    # Brand filtering
    if brand:
        query += " AND ("
        multi_query = f"brand ="
        for i in brand:
            query += f"{multi_query} '{i}' OR "
        query = query[:-4] + ')'

    
    # Budget constraint
    if budget:
        if budget[0] == '<':
            query += f" AND {compare_budget_to} <= {float(budget[1:-1])}"
        else:
            query += f" AND {compare_budget_to} > {float(budget[1:-1])}"

    
    # Positive preferences (like)
    if like:
        # Use ILIKE for case-insensitive partial matching
        query += f" AND ("
        like_clauses = [f"description ILIKE '%{condition}%'" for condition in like]
        query += " OR ".join(like_clauses)
        query += ")"
    
    # Negative preferences (dislike)
    if dislike:
        # Exclude products with these characteristics
        query += f" AND ("
        dislike_clauses = [f"description NOT ILIKE '%{condition}%'" for condition in dislike]
        query += " AND ".join(dislike_clauses)
        query += ")"
    
    # Add ordering and limit
    query += f"""
    ORDER BY {compare_budget_to} ASC
    LIMIT 10;
    """
    
    return query

example_query = generate_product_search_query(
    objective=data['objective'], 
    brand=data['brand'], 
    budget=data['budget'], 
    like=data['preferences']['yes'], 
    dislike=data['preferences']['no']
)

print(example_query)