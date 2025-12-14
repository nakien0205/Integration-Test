"""
Minimal API server that works without complex dependencies
Run this while you configure your environment
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid

app = FastAPI(title="Shopping Assistant API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    content: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    session_id: str
    message: str
    products: Optional[List[Dict[str, Any]]] = None
    end_chat: bool = False

@app.post("/api/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Handle chat messages"""
    session_id = message.session_id or str(uuid.uuid4())
    
    # Mock product response
    mock_products = [
        {
            "asin": "B08N5WRWNW",
            "title": "Gaming Laptop - Example Product",
            "brand": "TechBrand",
            "price": "$999.99",
            "rating": 4.5,
            "rating_count": "1,234",
            "images": '["https://via.placeholder.com/300"]',
            "availability": "In Stock"
        }
    ]
    
    response_message = f"I understand you're looking for: '{message.content}'. Here are some products I found (Note: This is test mode - configure .env for real AI responses):"
    
    return ChatResponse(
        session_id=session_id,
        message=response_message,
        products=mock_products
    )

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "mode": "test",
        "message": "Test server running. Configure .env for full features."
    }

@app.get("/")
async def root():
    return {
        "message": "Shopping Assistant API",
        "status": "running",
        "mode": "test",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("🚀 Starting Shopping Assistant API (TEST MODE)")
    print("=" * 60)
    print("✅ Backend: http://localhost:8000")
    print("✅ API Docs: http://localhost:8000/docs")
    print("✅ Health: http://localhost:8000/api/health")
    print("=" * 60)
    print("📝 Note: This is test mode with mock responses")
    print("💡 To enable full AI features:")
    print("   1. Configure your .env file with API keys")
    print("   2. Fix dependency conflicts (lxml/crawl4ai)")
    print("   3. Use: python -m uvicorn api:app --reload")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)
