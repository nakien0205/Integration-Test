from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import inspect
import uuid
import uvicorn
from main.tools import all_tools
from database.store_chat import store_message, retrieve_chat_history
from main.main import search_web, get_product_data

# --- init ---
load_dotenv()
client = OpenAI(
    base_url="https://openrouter.ai/api/v1", 
    api_key=os.environ.get("API")
)
model_name = "meta-llama/llama-4-maverick:free"

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080", 
        "http://127.0.0.1:8080",
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sys_prompt = """
You are a helpful shopping assistant. 
When discussing products, use the get_product_data tool to retrieve accurate product information.
If the user clearly wants to end the conversation, respond exactly with the token END_CHAT.
"""
tool_functions = {
    "search_web": search_web,
    "get_product_data": get_product_data,
}

# Store sessions in memory (consider using Redis for production)
sessions: Dict[str, List[Dict]] = {}

class Message(BaseModel):
    content: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    session_id: str
    message: str
    products: Optional[List[Dict[str, Any]]] = None
    end_chat: bool = False

def initialize_session(session_id: str):
    """Initialize a new chat session"""
    sessions[session_id] = [
        {
            "role": "system", 
            "content": sys_prompt
        }
    ]
    store_message(session_id, "system", sys_prompt)

def extract_products_from_tool_result(result: Any) -> Optional[List[Dict]]:
    """Extract product information from tool results"""
    if not result:
        return None
    
    if isinstance(result, list):
        products = []
        for item in result:
            if isinstance(item, dict) and any(key in item for key in ['title', 'price', 'asin']):
                products.append(item)
        return products if products else None
    
    return None

@app.post("/api/chat", response_model=ChatResponse)
async def chat(message: Message):
    """Handle chat messages and return responses with products"""
    try:
        # Initialize or get session
        session_id = message.session_id or str(uuid.uuid4())
        
        if session_id not in sessions:
            initialize_session(session_id)
        
        chat_history = sessions[session_id]
        
        # Add user message
        chat_history.append({"role": "user", "content": message.content})
        store_message(session_id, "user", message.content)
        
        # Get AI response
        first = client.chat.completions.create(
            model=model_name,
            messages=chat_history,
            tools=all_tools,
            tool_choice="auto"
        )
        msg = first.choices[0].message
        
        # Check if conversation should end
        # if msg.content == 'END_CHAT':
        #     return ChatResponse(
        #         session_id=session_id,
        #         message="Thank you for using ShopGPT! Have a great day!",
        #         end_chat=True
        #     )
        
        products_list = []
        
        # Handle tool calls
        if msg.tool_calls:
            tool_calls_data = [tc.model_dump() for tc in msg.tool_calls]
            chat_history.append({
                "role": "assistant",
                "tool_calls": tool_calls_data,
                "content": msg.content or ""
            })
            store_message(session_id, "assistant", msg.content or "", tool_calls=tool_calls_data)
            
            for tc in msg.tool_calls:
                fn_name = tc.function.name
                fn = tool_functions.get(fn_name)
                
                if not fn:
                    continue
                
                args = json.loads(tc.function.arguments or "{}")
                sig = inspect.signature(fn)
                call_args = {
                    k: args[k] if k in args else v.default
                    for k, v in sig.parameters.items()
                    if k in args or v.default is not inspect._empty
                }
                
                result = fn(**call_args)
                
                # Extract products from tool result
                if fn_name == 'get_product_data':
                    extracted_products = extract_products_from_tool_result(result)
                    if extracted_products:
                        products_list.extend(extracted_products)
                
                # Add tool message to history
                tool_message = {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": fn_name,
                    "content": json.dumps(result, ensure_ascii=False)
                }
                chat_history.append(tool_message)
            
            # Get final response
            followup = client.chat.completions.create(
                model=model_name,
                messages=chat_history
            )
            final_msg = followup.choices[0].message.content or ""
            chat_history.append({"role": "assistant", "content": final_msg})
            store_message(session_id, "assistant", final_msg)
            
            return ChatResponse(
                session_id=session_id,
                message=final_msg,
                products=products_list if products_list else None
            )
        else:
            # No tools used
            text = msg.content or ""
            chat_history.append({"role": "assistant", "content": text})
            store_message(session_id, "assistant", text)
            
            return ChatResponse(
                session_id=session_id,
                message=text
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history/{session_id}")
async def get_history(session_id: str):
    """Retrieve chat history for a session"""
    try:
        history = retrieve_chat_history(session_id)
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
