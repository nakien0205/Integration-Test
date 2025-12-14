import os
from supabase import create_client, Client
from dotenv import load_dotenv
import uuid

# --- Load environment variables ---
load_dotenv()

# --- Supabase connection ---
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_CONTROL_KEY")
email = os.environ.get("EMAIL")
password = os.environ.get("PASSWORD")

supabase: Client = create_client(url, key)

if supabase:
    print("Supabase connection established.")

def generate_conversation_id():
    return str(uuid.uuid4())

def sign_in():
    """Sign in an existing user."""
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        print("Sign-in successful!")
        return response
    except Exception as e:
        return print(f"Sign-in error: {e}")


def sign_out():
    """Sign out the current user."""
    try:
        supabase.auth.sign_out()
        print("Signed out.")
    except Exception as e:
        print(f"Sign-out error: {e}")


def store_message(conversation_id, role, content, tool_calls=None):
    """
    Stores a chat message in the Supabase database.
    """
    try:
        data = {
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "tool_calls": tool_calls,
            "country": ''
        }

        response = supabase.table("chat_history").insert(data).execute()
        return response

    except Exception as e:
        return print(f"Error storing message: {e}")


def retrieve_chat_history(conversation_id=None):
    """
    Retrieves chat history from the Supabase database.
    """
    try:
        query = supabase.table("chat_history").select("*")

        if conversation_id:
            query = query.eq("conversation_id", conversation_id)

        response = query.order("time").execute()
        return response.data

    except Exception as e:
        print(f"Error retrieving chat history: {e}")
        return []

# answer = retrieve_chat_history('77c94a38-8572-4703-976e-2357e77e2cc8')

# for i in answer:
#     if i['role'] == 'user':
#         print(f'User: {i["content"]}')
#     elif i['role'] == 'assistant':
#         print(f'AI: {i["content"]}')
#         print('-' * 100)