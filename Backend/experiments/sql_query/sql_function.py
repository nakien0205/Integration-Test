import os
from supabase import create_client, Client
from dotenv import load_dotenv
import json
from typing import *
from openai import OpenAI

load_dotenv()

database_url = os.environ.get("SUPABASE_URL")
database_key = os.environ.get("SUPABASE_KEY")
openai_key = os.environ.get('OPENAI_KEY')

supabase: Client = create_client(database_url, database_key)

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

def search_products(prompt: str, limit: int = 10, offset: int = 0) -> Dict:
    """
    Search products based on a text prompt with pagination support.
    
    Args:
        prompt: The user's search query in natural language
        limit: Maximum number of results to return (default: 10)
        offset: Number of results to skip for pagination (default: 0)
        
    Returns:
        Dict: A structured response with the following keys:
            - success: Boolean indicating if the search was successful
            - data: List of product data
            - count: Number of products returned
            - query_params: The parameters used for the search
    """
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

    params = {
        'title_search': data['objective'] if data['objective'] else None,
        'brands_filter': data['brand'] if data['brand'] else None,
        'max_price': float(data['budget'][1:-1]) if data['budget'] else None,
        'desc_includes': data['preferences']['yes'] if data['preferences']['yes'] else None,
        'desc_excludes': data['preferences']['no'] if data['preferences']['no'] else None,
        'result_limit': limit,
        'result_offset': offset
    }

    try:
        # For existing function, we'll remove pagination params and handle it in Python
        search_params = {
            'title_search': params['title_search'],
            'brands_filter': params['brands_filter'],
            'max_price': params['max_price'],
            'desc_includes': params['desc_includes'],
            'desc_excludes': params['desc_excludes']
        }
        
        try:
            # Try to use the count function if it exists
            count_response = supabase.rpc('count_matching_products', search_params).execute()
            total_count = count_response.data[0]['count'] if count_response.data else 0
        except Exception:
            # If count function doesn't exist, we'll get all results and count them
            total_count = None
            
        try:
            # Try with pagination parameters if the updated function exists
            search_response = supabase.rpc('search_products', params).execute()
            response = search_response
        except Exception:
            # Fallback to the original function and handle pagination in Python
            full_response = supabase.rpc('search_products', search_params).execute()
            
            # Manual pagination in Python
            if full_response.data:
                # Set total count if we couldn't get it from the count function
                if total_count is None:
                    total_count = len(full_response.data)
                
                # Apply pagination manually
                paginated_data = full_response.data[offset:offset+limit] if offset < len(full_response.data) else []
                response = type('obj', (object,), {'data': paginated_data})
        
        # Structure the response
        result = {
            "success": True,
            "data": response.data,
            "count": len(response.data) if response.data else 0,
            "total_count": total_count,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "has_more": (offset + limit) < total_count
            },
            "query_params": params
        }
        
        return result

    except Exception as e:
        error_response = {
            "success": False,
            "error": str(e),
            "data": None,
            "count": 0,
            "total_count": 0,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "has_more": False
            },
            "query_params": params
        }
        return error_response
        
# Example usage
if __name__ == "__main__":
    example_prompt = 'I want an AC power cord from OMNIHIL'
    
    # First page (5 results)
    print("=== Page 1 ===")
    result1 = search_products(example_prompt, limit=5, offset=0)
    print(f"Success: {result1['success']}")
    print(f"Items on this page: {result1['count']}")
    print(f"Total matching items: {result1['total_count']}")
    print(f"Has more pages: {result1['pagination']['has_more']}")
    
    # If we have more results, get the next page
    if result1['pagination']['has_more']:
        print("\n=== Page 2 ===")
        result2 = search_products(example_prompt, limit=5, offset=5)
        print(f"Success: {result2['success']}")
        print(f"Items on this page: {result2['count']}")
        print(f"Total matching items: {result2['total_count']}")
        print(f"Has more pages: {result2['pagination']['has_more']}")