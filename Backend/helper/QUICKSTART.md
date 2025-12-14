# 🚀 Quick Start Guide - ShopGPT Integration

## Current Status

✅ **Frontend**: Running on http://localhost:8080  
⚠️ **Backend**: Needs environment configuration

## Step-by-Step Setup

### Option 1: Test Mode (Quick Demo)

If you just want to see the integration working without full AI/database setup:

1. **Start the test backend** (in a new terminal):
   ```powershell
   cd "d:\Python\Projects\Shopping"
   .venv\Scripts\Activate.ps1
   python api_test.py
   ```

2. **Frontend is already running** on http://localhost:8080

3. **Test it**: Open http://localhost:8080 and type a message. You'll get mock responses!

### Option 2: Full Integration (With AI & Database)

For the complete experience with AI and real product search:

1. **Configure your environment**:
   - A `.env` file has been created at `d:\Python\Projects\Shopping\.env`
   - Open it and fill in your actual credentials:
   
   ```env
   # OpenRouter API Key (get from https://openrouter.ai/)
   API=your_actual_openrouter_api_key_here
   
   # Supabase Configuration (get from https://supabase.com/)
   SUPABASE_URL=https://yourproject.supabase.co
   SUPABASE_KEY=your_supabase_anon_key_here
   SUPABASE_CONTROL_KEY=your_supabase_service_role_key_here
   
   # Supabase Auth
   EMAIL=your_email@example.com
   PASSWORD=your_password_here
   ```

2. **Start the full backend** (in a new terminal):
   ```powershell
   cd "d:\Python\Projects\Shopping"
   .venv\Scripts\Activate.ps1
   python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Frontend is already running** on http://localhost:8080

4. **Start chatting!** Ask about products and see the AI-powered search in action.

## 🎯 What's Been Integrated

### Backend (`api.py`)
- ✅ FastAPI server with CORS enabled
- ✅ Chat endpoint that handles conversations
- ✅ Integration with your `main.py` AI logic
- ✅ Tool calling (search_web, get_product_data)
- ✅ Product retrieval from database or web scraping
- ✅ Session management
- ✅ Chat history storage

### Frontend (`front_end/src/pages/Index.tsx`)
- ✅ Updated to call backend API instead of direct Supabase queries
- ✅ Session management for continuous conversations
- ✅ Product card display
- ✅ Loading states
- ✅ Error handling

### Communication Flow
```
User Input (Frontend)
    ↓
POST /api/chat (Backend API)
    ↓
OpenAI/OpenRouter (AI Processing)
    ↓
Tool Calls (get_product_data, search_web)
    ↓
Database Search (BM25 algorithm)
    ↓ (if no results)
Web Scraping (Crawl4AI)
    ↓
Response with Products (JSON)
    ↓
Display Products (Frontend)
```

## 🐛 Troubleshooting

### Backend won't start - "Invalid URL" error
**Solution**: You need to configure your `.env` file with actual Supabase credentials.
- Use **Option 1 (Test Mode)** to test the integration without credentials
- Or get your Supabase credentials from https://supabase.com/

### Frontend can't connect to backend
**Solution**: Make sure the backend is running on port 8000
- Check terminal for "Uvicorn running on http://0.0.0.0:8000"
- Try accessing http://localhost:8000/api/health in your browser

### CORS errors
**Solution**: Already configured! The backend allows requests from localhost:8080

### Port already in use
**Solution**: 
```powershell
# Find and kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <process_id> /F
```

## 📁 Files Created/Modified

### New Files
- `api.py` - Main FastAPI backend server with full integration
- `api_test.py` - Simple test server for demo without credentials
- `.env` - Environment configuration (needs your credentials)
- `.env.example` - Template for environment variables
- `front_end/.env.example` - Frontend environment template
- `INTEGRATION_README.md` - Complete documentation
- `QUICKSTART.md` - This file!

### Modified Files
- `front_end/src/pages/Index.tsx` - Updated to use backend API

## 🧪 Testing the Integration

### Test 1: Health Check
```bash
# In browser or terminal:
curl http://localhost:8000/api/health
# Should return: {"status":"healthy"}
```

### Test 2: Chat Endpoint
```bash
# Send a test chat message:
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"content":"Show me gaming laptops"}'
```

### Test 3: Frontend to Backend
1. Open http://localhost:8080
2. Type "I want to buy a laptop"
3. Check browser console (F12) for API calls
4. Check backend terminal for request logs

## 🎉 Next Steps

Once everything is working:

1. **Customize the AI prompt** in `api.py` (line 34)
2. **Adjust product search parameters** in `main/finder.py`
3. **Modify the UI** in `front_end/src/components/`
4. **Add more features**:
   - Product comparison
   - Price tracking
   - User preferences
   - Favorites list

## 📚 Documentation

- Full documentation: `INTEGRATION_README.md`
- API endpoints: http://localhost:8000/docs (when server is running)
- Frontend components: See `front_end/src/components/`

## 💡 Tips

- Use **Test Mode** first to verify everything is connected correctly
- The AI uses the Llama 4 Maverick model (free via OpenRouter)
- Search results use BM25 algorithm for relevance ranking
- If database search finds nothing, it automatically triggers web scraping
- All conversations are saved to your Supabase database

## ❓ Need Help?

Check the error logs in:
- Backend terminal (shows API errors, AI responses)
- Frontend terminal (shows build/runtime errors)
- Browser console (F12, shows network requests)

---

**Current Status**: Frontend is running! Start the backend using one of the options above.
