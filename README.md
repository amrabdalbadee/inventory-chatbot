# Inventory Chatbot 

A minimal AI chat service with **Ollama as the default provider**. Automatically switches to OpenAI/Azure if credentials are provided in `.env`.

## Requirements

- Python 3.10+
- `pydantic`
- `openai` (official SDK - works with Ollama too)

## Installation

```bash
pip install pydantic openai
```

### Option 1: Use Ollama (Free, Local - Default)
```bash
# Install Ollama - https://ollama.ai
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama3.2

# Start Ollama (if not running)
ollama serve
```

### Option 2: Use OpenAI (Paid API)
Just add your API key to `.env`:
```env
OPENAI_API_KEY=sk-your-key-here
MODEL_NAME=gpt-4o-mini
```

## Configuration

Edit the `.env` file in the project directory:

```env
# Leave empty to use Ollama (default)
OPENAI_API_KEY=

# Or set your OpenAI key to use OpenAI instead
OPENAI_API_KEY=sk-...

# Or set Azure credentials (takes priority)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=your-deployment

# Model name
MODEL_NAME=llama3.2

# Ollama URL (if not default)
OLLAMA_BASE_URL=http://localhost:11434

# Server port
PORT=8000
```

## Provider Priority

The system automatically detects which provider to use:

1. **Azure OpenAI** - if `AZURE_OPENAI_API_KEY` and `AZURE_OPENAI_ENDPOINT` are set
2. **OpenAI** - if `OPENAI_API_KEY` is set
3. **Ollama** - default fallback (no API key needed)

## Running

```bash
cd inventory-chatbot-v2
python server.py
```

Output:
```
========================================================
  Inventory Chatbot Server
========================================================
  Open in browser: http://localhost:8000
  Provider: ollama
  Model:    llama3.2
========================================================
  Press Ctrl+C to stop
```

**Important**: Open `http://localhost:8000` in your browser (not `0.0.0.0:8000`).

## Usage

### Web UI
Open `http://localhost:8000` in your browser. The status badge shows which provider is active.

### API
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "message": "How many assets do I have?"}'
```

### Status Endpoint
```bash
curl http://localhost:8000/api/status
# {"status": "running", "provider": "ollama", "model": "llama3.2"}
```

## Project Structure

```
inventory-chatbot-v2/
├── .env            # Configuration file
├── server.py       # REST API server (includes embedded HTML)
├── llm_client.py   # Multi-provider LLM client
├── env_loader.py   # .env file parser
├── models.py       # Pydantic models
├── schema.py       # SQL Server DDL
└── README.md
```

## Features

- ✅ Ollama as default (no API key required)
- ✅ Automatic provider detection
- ✅ Configuration via `.env` file
- ✅ REST API (`POST /api/chat`, `GET /api/status`)
- ✅ OpenAI & Azure OpenAI support
- ✅ In-memory session management
- ✅ SQL query generation ("present query")
- ✅ Token usage tracking
- ✅ Response latency measurement
- ✅ Web-based chat UI with provider indicator
- ✅ No external dependencies (except pydantic & openai SDK)
