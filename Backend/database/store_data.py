import os
from supabase import create_client, Client
from dotenv import load_dotenv

# --- Load environment variables ---
load_dotenv()

# --- Supabase connection ---
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_CONTROL_KEY")
email = os.environ.get("EMAIL")
password = os.environ.get("PASSWORD")

# Lazy initialization - only create client when actually used
_supabase_client = None

def get_supabase_client():
    """Get or create Supabase client lazily."""
    global _supabase_client
    if _supabase_client is None:
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_CONTROL_KEY must be set in .env file")
        _supabase_client = create_client(url, key)
    return _supabase_client

def store_data(asin, title, brand, price, discount, rating, rating_count, availability, info, product_description, images, return_policy):
    """
    Store scraped data in the Supabase database.
    """
    try:
        supabase = get_supabase_client()
        data = {
            "asin": asin,
            "title": title,
            "brand": brand,
            "price": price,
            "discount": discount,
            "rating": rating,
            "rating_count": rating_count,
            "availability": availability,
            "info": info,
            "product_description": product_description,
            "images": images,
            "return_policy": return_policy,
        }

        response = supabase.table("testing").insert(data).execute()
        return response

    except Exception as e:
        return print(f"Error storing message: {e}")
    

def retrieve_data():
    """
    Retrieves data from the Supabase database.
    """
    try:
        supabase = get_supabase_client()
        query = supabase.table("data").select("*")
        response = query.execute()
        return response.data

    except Exception as e:
        print(f"Error retrieving chat history: {e}")
        return []