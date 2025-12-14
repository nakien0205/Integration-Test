# 🚀 How to Run the Shopping Assistant Project

This guide will help you run both the backend and frontend of your Shopping Assistant application.

## 📋 Prerequisites

Before running the project, ensure you have:

- **Python 3.8+** installed
- **Node.js 18+** and **npm** installed
- **Git** (if cloning from repository)

## 🔧 Initial Setup (First Time Only)

### 1. Install Backend Dependencies

Open a terminal in the project root directory:

```bash
# Install Python dependencies
pip install -r requirements.txt
```

### 2. Install Frontend Dependencies

```bash
# Navigate to frontend directory
cd front_end

# Install npm packages
npm install

# Return to project root
cd ..
```

### 3. Configure Environment Variables

Create a `.env` file in the project root and add your credentials:

```bash
# Copy the example file
copy .env.example .env
```

Then edit `.env` with your actual credentials:

```env
# OpenRouter API (Required for AI features)
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Supabase Database (Required for data storage)
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key

# Optional: Custom OpenRouter Base URL
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

**Where to get credentials:**
- **OpenRouter API Key**: Sign up at https://openrouter.ai/
- **Supabase**: Create a free project at https://supabase.com/

## ▶️ Running the Project

You need to run **TWO servers** simultaneously:

### Option A: Using Two Terminals (Recommended)

#### Terminal 1 - Backend Server

```bash
# From project root
python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

**Backend will run at:** http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

#### Terminal 2 - Frontend Server

```bash
# Navigate to frontend
cd front_end

# Start development server
npm run dev
```

**Frontend will run at:** http://localhost:8080

### Option B: Using PowerShell Script

Create a file named `run.ps1` in the project root:

```powershell
# Start backend in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload"

# Wait a bit for backend to start
Start-Sleep -Seconds 3

# Start frontend in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd front_end; npm run dev"

Write-Host "✅ Both servers starting..."
Write-Host "Backend: http://localhost:8000"
Write-Host "Frontend: http://localhost:8080"
```

Then run:
```bash
.\run.ps1
```

### Option C: Test Mode (No Credentials Required)

If you don't have API credentials yet, you can run in test mode:

#### Terminal 1 - Test Backend
```bash
python api_test.py
```

#### Terminal 2 - Frontend
```bash
cd front_end
npm run dev
```

## 🎯 Accessing the Application

Once both servers are running:

1. **Open your browser** to http://localhost:8080
2. **Start chatting** with the shopping assistant
3. **Ask for products** like "Find me running shoes under $100"

## 🛑 Stopping the Servers

Press `Ctrl + C` in each terminal window to stop the servers.

## 🔍 Verifying Everything Works

### Check Backend Health

```bash
curl http://localhost:8000/health
```

Should return:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-05T..."
}
```

### Check Frontend

Open http://localhost:8080 - you should see the chat interface.

### Test API Integration

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Hello\", \"session_id\": \"test123\"}"
```

## 📁 Project Structure

```
Shopping/
├── api.py                 # Main FastAPI backend
├── api_test.py           # Test backend (no credentials needed)
├── .env                  # Your credentials (DO NOT COMMIT)
├── requirements.txt      # Python dependencies
├── front_end/
│   ├── package.json     # Frontend dependencies
│   ├── src/
│   │   └── pages/
│   │       └── Index.tsx # Main chat interface
│   └── ...
├── main/
│   └── main.py          # Core AI logic
├── database/
│   └── store_data.py    # Database operations
└── ...
```

## 🐛 Troubleshooting

### Backend Issues

**Error: "No module named 'fastapi'"**
```bash
pip install -r requirements.txt
```

**Error: "Connection to Supabase failed"**
- Check your `.env` file has correct credentials
- Verify Supabase project is active

**Port 8000 already in use**
```bash
# Use a different port
python -m uvicorn api:app --port 8001 --reload
```

### Frontend Issues

**Error: "npm: command not found"**
- Install Node.js from https://nodejs.org/

**Port 8080 already in use**
- The dev server will automatically try port 8081

**Error: "Cannot connect to backend"**
- Ensure backend is running on port 8000
- Check `.env.local` has correct API URL

### Database Issues

**No products found**
- The system will automatically scrape Amazon if database is empty
- First query may take longer (30-60 seconds)

**Supabase connection errors**
- Verify credentials in `.env`
- Check Supabase project status

## 🔄 Development Workflow

1. **Make changes** to backend: [`api.py`](api.py ) or files in [`main/`](main/ ), [`database/`](database/ ), etc.
   - Backend auto-reloads (if using `--reload` flag)

2. **Make changes** to frontend: Files in [`front_end/src/`](front_end/src/ )
   - Frontend auto-reloads via Vite HMR

3. **Test changes** in browser at http://localhost:8080

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs (when backend is running)
- **Backend Code**: [`api.py`](api.py )
- **Frontend Code**: [`front_end/src/pages/Index.tsx`](front_end/src/pages/Index.tsx )
- **Main AI Logic**: [`main/main.py`](main/main.py )
- **Integration Guide**: [`INTEGRATION_README.md`](INTEGRATION_README.md )

## 🚀 Quick Start Summary

```bash
# 1. Install dependencies (first time only)
pip install -r requirements.txt
cd front_end && npm install && cd ..

# 2. Configure .env file with your credentials

# 3. Run backend (Terminal 1)
python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload

# 4. Run frontend (Terminal 2)
cd front_end && npm run dev

# 5. Open browser to http://localhost:8080
```

---

**Need help?** Check the troubleshooting section or review [`INTEGRATION_README.md`](INTEGRATION_README.md ) for more details.