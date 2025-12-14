# ShopGPT - Integrated Shopping Assistant

This is a full-stack shopping assistant application with AI-powered product search and comparison.

## Architecture

- **Backend**: FastAPI (Python) - Handles AI chat, product search, and web scraping
- **Frontend**: React + Vite + TypeScript - Modern web interface
- **Database**: Supabase - Stores product data and chat history
- **AI**: OpenRouter API (Llama 4 Maverick) - Powers the conversational interface

## Features

- 🤖 AI-powered conversational interface
- 🔍 Smart product search across multiple sources
- 🛒 Product comparison with detailed information
- 💾 Persistent chat history
- 🌐 Web scraping for real-time product data
- 📊 BM25-based search ranking

## Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- Supabase account
- OpenRouter API key

## Setup Instructions

### 1. Backend Setup

1. **Create and activate virtual environment** (if not already done):
   ```bash
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   - Copy `.env.example` to `.env`
   - Fill in your credentials:
     - `API`: Your OpenRouter API key
     - `SUPABASE_URL`: Your Supabase project URL
     - `SUPABASE_KEY`: Your Supabase anon key
     - `SUPABASE_CONTROL_KEY`: Your Supabase service role key
     - `EMAIL` and `PASSWORD`: Supabase auth credentials

4. **Run the backend server**:
   ```bash
   python api.py
   ```
   The backend will be available at `http://localhost:8000`

### 2. Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd front_end
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure environment variables** (optional):
   - Copy `.env.example` to `.env`
   - Update `VITE_API_BASE_URL` if your backend runs on a different port

4. **Run the development server**:
   ```bash
   npm run dev
   ```
   The frontend will be available at `http://localhost:8080`

## Usage

1. Start both servers (backend on port 8000, frontend on port 8080)
2. Open your browser to `http://localhost:8080`
3. Start chatting with ShopGPT!
4. Ask about products, and the AI will search and compare them for you

### Example Queries

- "I'm looking for a gaming laptop under $1500"
- "Compare the latest iPhone models"
- "Show me wireless headphones with noise cancellation"
- "What are the best budget smartphones?"

## API Endpoints

### POST `/api/chat`
Send a chat message and receive AI response with product data.

**Request Body**:
```json
{
  "content": "I want to buy a laptop",
  "session_id": "optional-session-id"
}
```

**Response**:
```json
{
  "session_id": "uuid",
  "message": "AI response text",
  "products": [
    {
      "asin": "B08N5WRWNW",
      "title": "Product Title",
      "brand": "Brand Name",
      "price": "$999.99",
      "rating": 4.5,
      "images": "[\"url1\", \"url2\"]",
      ...
    }
  ],
  "end_chat": false
}
```

### GET `/api/history/{session_id}`
Retrieve chat history for a session.

### GET `/api/health`
Health check endpoint.

## Project Structure

```
Shopping/
├── api.py                  # FastAPI backend server
├── main/
│   ├── main.py            # Original CLI chat interface
│   ├── finder.py          # Product search engine (BM25)
│   └── tools.py           # AI tool definitions
├── crawler/
│   ├── crawl.py           # Web scraping logic
│   └── schema.py          # Data schemas
├── database/
│   ├── store_chat.py      # Chat history storage
│   └── store_data.py      # Product data storage
├── front_end/
│   ├── src/
│   │   ├── pages/
│   │   │   └── Index.tsx  # Main chat interface
│   │   ├── components/    # UI components
│   │   └── ...
│   └── package.json
└── requirements.txt
```

## Technologies Used

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **OpenAI SDK**: For interacting with OpenRouter API
- **Supabase**: Backend as a Service for database
- **Beautiful Soup**: Web scraping
- **Pandas**: Data manipulation
- **DuckDuckGo Search**: Web search functionality

### Frontend
- **React 18**: UI library
- **Vite**: Build tool and dev server
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first CSS framework
- **shadcn/ui**: Beautiful, accessible UI components
- **TanStack Query**: Data fetching and caching

## Troubleshooting

### Backend Issues

1. **ModuleNotFoundError**: Make sure all dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```

2. **API key errors**: Verify your `.env` file has the correct API keys

3. **Port already in use**: Change the port in `api.py` or kill the process using port 8000

### Frontend Issues

1. **Cannot connect to backend**: Ensure the backend is running on port 8000

2. **CORS errors**: Check that CORS is properly configured in `api.py`

3. **npm install fails**: Try clearing npm cache:
   ```bash
   npm cache clean --force
   npm install
   ```

## Development

### Running Tests
```bash
# Backend tests
python -m pytest

# Frontend tests
cd front_end
npm test
```

### Building for Production

**Frontend**:
```bash
cd front_end
npm run build
```

**Backend**: Use a production ASGI server like Gunicorn:
```bash
pip install gunicorn
gunicorn api:app -w 4 -k uvicorn.workers.UvicornWorker
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is for educational purposes.

## Support

For issues and questions, please open an issue on GitHub.
