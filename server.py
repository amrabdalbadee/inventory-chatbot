"""REST API server using Python standard library."""
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from pathlib import Path

# Load .env file FIRST before other imports
from env_loader import load_env, get_env

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.resolve()
load_env(SCRIPT_DIR / ".env")

from models import ChatRequest, ChatResponse
from llm_client import LLMClient

# In-memory session storage
sessions: dict[str, list[dict]] = {}
llm_client: LLMClient = None

# Embedded HTML (always works regardless of file location)
EMBEDDED_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Inventory Chatbot</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; height: 100vh; display: flex; flex-direction: column; }
        header { background: #1a73e8; color: white; padding: 16px 24px; display: flex; justify-content: space-between; align-items: center; }
        header h1 { font-size: 20px; font-weight: 500; }
        .status { font-size: 12px; background: rgba(255,255,255,0.2); padding: 6px 12px; border-radius: 16px; }
        .status.ollama { background: #ff6b35; }
        .status.openai { background: #10a37f; }
        .status.azure { background: #0078d4; }
        .container { flex: 1; display: flex; flex-direction: column; max-width: 900px; margin: 0 auto; width: 100%; padding: 16px; overflow: hidden; }
        .chat-box { flex: 1; overflow-y: auto; background: white; border-radius: 8px; padding: 16px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .message { margin-bottom: 16px; }
        .message.user { text-align: right; }
        .message .bubble { display: inline-block; max-width: 80%; padding: 12px 16px; border-radius: 16px; text-align: left; }
        .message.user .bubble { background: #1a73e8; color: white; border-bottom-right-radius: 4px; }
        .message.assistant .bubble { background: #e8f0fe; color: #333; border-bottom-left-radius: 4px; }
        .sql-block { background: #263238; color: #aed581; padding: 12px; border-radius: 8px; margin-top: 8px; font-family: monospace; font-size: 13px; overflow-x: auto; white-space: pre-wrap; }
        .meta { font-size: 11px; color: #666; margin-top: 8px; }
        .input-area { display: flex; gap: 8px; }
        .input-area input { flex: 1; padding: 14px 16px; border: 1px solid #ddd; border-radius: 24px; font-size: 15px; outline: none; }
        .input-area input:focus { border-color: #1a73e8; }
        .input-area button { padding: 14px 24px; background: #1a73e8; color: white; border: none; border-radius: 24px; font-size: 15px; cursor: pointer; }
        .input-area button:hover { background: #1557b0; }
        .input-area button:disabled { background: #ccc; cursor: not-allowed; }
        .loading { display: inline-block; width: 20px; height: 20px; border: 2px solid #ccc; border-top-color: #1a73e8; border-radius: 50%; animation: spin 1s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
        .examples { padding: 8px 0; color: #666; font-size: 13px; }
        .examples span { cursor: pointer; color: #1a73e8; margin-right: 12px; }
        .examples span:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <header>
        <h1>📦 Inventory Analytics Chatbot</h1>
        <div class="status" id="statusBadge">Loading...</div>
    </header>
    <div class="container">
        <div class="chat-box" id="chatBox">
            <div class="examples">
                Try: 
                <span onclick="ask('How many assets do I have?')">How many assets?</span>
                <span onclick="ask('How many assets by site?')">Assets by site</span>
                <span onclick="ask('How many open purchase orders?')">Open POs</span>
                <span onclick="ask('Total value of assets per site?')">Asset values</span>
            </div>
        </div>
        <div class="input-area">
            <input type="text" id="userInput" placeholder="Ask about inventory, assets, orders..." onkeypress="if(event.key==='Enter')sendMessage()">
            <button id="sendBtn" onclick="sendMessage()">Send</button>
        </div>
    </div>
    <script>
        const sessionId = 'session-' + Math.random().toString(36).substr(2, 9);
        const chatBox = document.getElementById('chatBox');
        const userInput = document.getElementById('userInput');
        const sendBtn = document.getElementById('sendBtn');
        const statusBadge = document.getElementById('statusBadge');

        async function fetchStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                statusBadge.textContent = data.provider + ' - ' + data.model;
                statusBadge.className = 'status ' + data.provider;
            } catch (e) {
                statusBadge.textContent = 'Disconnected';
            }
        }
        fetchStatus();

        function addMessage(content, type, sql, meta) {
            const div = document.createElement('div');
            div.className = 'message ' + type;
            let html = '<div class="bubble">' + escapeHtml(content) + '</div>';
            if (sql) {
                html += '<div class="sql-block">' + escapeHtml(sql) + '</div>';
            }
            if (meta) {
                html += '<div class="meta">' + meta + '</div>';
            }
            div.innerHTML = html;
            chatBox.appendChild(div);
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function ask(question) {
            userInput.value = question;
            sendMessage();
        }

        async function sendMessage() {
            const message = userInput.value.trim();
            if (!message) return;

            addMessage(message, 'user', null, null);
            userInput.value = '';
            sendBtn.disabled = true;
            sendBtn.innerHTML = '<span class="loading"></span>';

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_id: sessionId, message: message })
                });
                const data = await response.json();

                if (data.status === 'ok') {
                    const meta = data.provider + ' | ' + data.model + ' | ' + data.latency_ms + 'ms | ' + data.token_usage.total_tokens + ' tokens';
                    addMessage(data.natural_language_answer, 'assistant', data.sql_query, meta);
                } else {
                    addMessage('Error: ' + (data.error_message || data.error || 'Unknown error'), 'assistant', null, null);
                }
            } catch (e) {
                addMessage('Network error: ' + e.message, 'assistant', null, null);
            }

            sendBtn.disabled = false;
            sendBtn.textContent = 'Send';
        }
    </script>
</body>
</html>'''


class RequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the chat API."""
    
    def _send_response(self, status: int, data: dict):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def _send_html(self, content: str):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def do_GET(self):
        path = urlparse(self.path).path
        
        if path == "/" or path == "/index.html":
            self._send_html(EMBEDDED_HTML)
        elif path == "/api/status":
            self._send_response(200, {
                "status": "running",
                "provider": llm_client.provider,
                "model": llm_client.model,
            })
        else:
            self._send_response(404, {"error": "Not found"})
    
    def do_POST(self):
        path = urlparse(self.path).path
        
        if path == "/api/chat":
            self._handle_chat()
        else:
            self._send_response(404, {"error": "Not found"})
    
    def _handle_chat(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            data = json.loads(body)
            
            # Validate request
            request = ChatRequest(**data)
            
            # Get or create session
            if request.session_id not in sessions:
                sessions[request.session_id] = []
            
            session_history = sessions[request.session_id]
            
            # Call LLM
            result = llm_client.chat(
                messages=[{"role": "user", "content": request.message}],
                session_history=session_history,
            )
            
            # Update session history
            if result["status"] == "ok":
                sessions[request.session_id].append({"role": "user", "content": request.message})
                sessions[request.session_id].append({
                    "role": "assistant",
                    "content": json.dumps({
                        "answer": result["natural_language_answer"],
                        "sql_query": result["sql_query"],
                    })
                })
                # Keep only last 10 exchanges
                sessions[request.session_id] = sessions[request.session_id][-20:]
            
            response = ChatResponse(**result)
            self._send_response(200, response.model_dump())
            
        except json.JSONDecodeError:
            self._send_response(400, {"error": "Invalid JSON"})
        except Exception as e:
            self._send_response(500, {"error": str(e)})
    
    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {args[0]}")


def run_server(host: str = "0.0.0.0", port: int = 8000):
    global llm_client
    llm_client = LLMClient()
    
    server = HTTPServer((host, port), RequestHandler)
    print()
    print("=" * 56)
    print("  Inventory Chatbot Server")
    print("=" * 56)
    print(f"  Open in browser: http://localhost:{port}")
    print(f"  Provider: {llm_client.provider}")
    print(f"  Model:    {llm_client.model}")
    print("=" * 56)
    print("  Press Ctrl+C to stop")
    print()
    server.serve_forever()


if __name__ == "__main__":
    port = int(get_env("PORT", "8000"))
    run_server(port=port)
