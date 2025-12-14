from openai import OpenAI
from dotenv import load_dotenv
import os, json, inspect, uuid
from ddgs import DDGS
from tools import all_tools
from finder import product_retriever
import os
from database.store_chat import store_message
from crawler.crawl import *

# --- init ---
load_dotenv()
client = OpenAI(
    base_url="https://openrouter.ai/api/v1", 
    api_key=os.environ.get("API")
)
model_name = "meta-llama/llama-4-maverick:free"

# --- session id ---
session_id = str(uuid.uuid4())

sys_prompt = """
    You are a helpful assistant. 
    If the user clearly wants to end the conversation, respond exactly with the token END_CHAT.
"""

chat_history = [
    {
        "role": "system", 
        "content": sys_prompt
    }
]
store_message(session_id, "system", sys_prompt)

# --- tool(s) ---
def search_web(search_query: str) -> list:
    return list(DDGS().text(search_query, max_results=3))

def get_product_data(search_query):
    database_answer = product_retriever(search_query)

    if database_answer:
        return database_answer
    else:
        data = crawl(search_query)
        return data

# It works fine, but the problem is that the scraping
tool_functions = {
    "search_web": search_web,
    "get_product_data": get_product_data,
}

# def scrape_or_not(user_input):
#     response = client.chat.completions.create(
#         model=model_name,
#         messages=[
#             {
#                 'role': 'system',
#                 'content': sys_prompt
#             },
#             {
#                 'role': 'user',
#                 'content': user_input
#             }
#         ]
#     )

#     return response.choices[0].message.content

# ---conversation loop ---
def chat(user_text):
    # # Crawl data
    # if scrape_or_not(user_text):
    #     additional_data = crawl(user_text)

    #     tool_message = {
    #         "tool_call_id": str(uuid.uuid4()),
    #         "role": "tool",
    #         "name": "web_scrape_data",
    #         "content": json.dumps(additional_data, ensure_ascii=False)
    #     }

    #     chat_history.append(tool_message)
    #     store_message(session_id, "tool", tool_message["content"], name="web_scrape_data")

    chat_history.append({"role": "user", "content": user_text})
    store_message(session_id, "user", user_text)

    first = client.chat.completions.create(
        model=model_name,
        messages=chat_history,
        tools=all_tools,
        tool_choice="auto"
    )
    msg = first.choices[0].message

    # If the model requested tool(s)
    if msg.tool_calls:
        stored_images = []
        # You must append the assistant message that contains the tool_calls
        tool_calls_data = [tc.model_dump() for tc in msg.tool_calls]
        chat_history.append(
            {
                "role": "assistant",
                "tool_calls": tool_calls_data,
                "content": msg.content or ""
            }
        )
        store_message(session_id, "assistant", msg.content or "", tool_calls=tool_calls_data)

        for tc in msg.tool_calls:
            fn_name = tc.function.name
            fn = tool_functions[fn_name]  # will KeyError if you forgot to map it


            args = json.loads(tc.function.arguments or "{}")
            # Call with signature-safe args
            sig = inspect.signature(fn)
            call_args = {
                k: args[k] if k in args else v.default
                for k, v in sig.parameters.items()
                if k in args or v.default is not inspect._empty
            }

            result = fn(**call_args)

            """
            This code gets the images links
            """
            # if fn_name == 'get_product_data':
            #     for data in result:
            #         if data['images']:
            #             stored_images.append(f"images: {data['images']}")

            # print(f'Stored images: ============================================================\n{stored_images}')
            # Tool messages must be strings
            tool_message = {
                "role": "tool",
                "tool_call_id": tc.id,
                "name": fn_name,
                "content": json.dumps(result, ensure_ascii=False)
            }
            chat_history.append(tool_message)

        # Now get the model's final reply that uses the tool outputs
        followup = client.chat.completions.create(
            model=model_name,
            messages=chat_history
        )
        final_msg = followup.choices[0].message.content or ""
        print(f"Assistant: {final_msg}")
        chat_history.append({"role": "assistant", "content": final_msg})
        store_message(session_id, "assistant", final_msg)

    else:
        # No tools used; just print and continue
        text = msg.content or ""
        print(f"Assistant: {text}")
        print('-' * 70 + '\n')
        chat_history.append({"role": "assistant", "content": text})
        store_message(session_id, "assistant", text)