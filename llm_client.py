"""LLM client with Ollama default, OpenAI/Azure optional."""
import json
import time
from typing import Literal

from openai import OpenAI, AzureOpenAI

from env_loader import get_env
from schema import SCHEMA_DDL

SYSTEM_PROMPT = f"""You are an inventory analytics assistant. Answer user questions about inventory, assets, customers, vendors, purchase orders, sales orders, and bills.

For EVERY response, you must provide:
1. A natural language answer to the user's question
2. The exact SQL Server query that would retrieve the data

DATABASE SCHEMA:
{SCHEMA_DDL}

RESPONSE FORMAT (strict JSON only, no markdown):
{{
    "answer": "Your natural language answer here",
    "sql_query": "SELECT ... FROM ... WHERE ..."
}}

RULES:
- Always exclude disposed assets unless explicitly asked (WHERE Status <> 'Disposed')
- Use proper SQL Server syntax (e.g., GETDATE(), DATEADD, TOP)
- For aggregations, use meaningful aliases
- If the question is unclear or not related to the schema, explain what you can help with and set sql_query to empty string
- Keep answers concise and professional
- IMPORTANT: Return ONLY valid JSON, no markdown code blocks
"""


class LLMClient:
    """Unified client supporting Ollama (default), OpenAI, and Azure OpenAI."""
    
    def __init__(self):
        self.provider: Literal["openai", "azure", "ollama"] = self._detect_provider()
        self.model = get_env("MODEL_NAME", "llama3.2")
        self.client = self._create_client()
    
    def _detect_provider(self) -> Literal["openai", "azure", "ollama"]:
        """Detect provider based on available credentials.
        
        Priority: Azure > OpenAI > Ollama (default)
        """
        azure_key = get_env("AZURE_OPENAI_API_KEY")
        azure_endpoint = get_env("AZURE_OPENAI_ENDPOINT")
        openai_key = get_env("OPENAI_API_KEY")
        
        if azure_key and azure_endpoint:
            return "azure"
        elif openai_key:
            return "openai"
        else:
            return "ollama"
    
    def _create_client(self):
        """Create the appropriate client based on provider."""
        if self.provider == "azure":
            self.model = get_env("AZURE_OPENAI_DEPLOYMENT", self.model)
            return AzureOpenAI(
                api_key=get_env("AZURE_OPENAI_API_KEY"),
                api_version="2024-02-15-preview",
                azure_endpoint=get_env("AZURE_OPENAI_ENDPOINT"),
            )
        elif self.provider == "openai":
            self.model = get_env("MODEL_NAME", "gpt-4o-mini")
            return OpenAI(api_key=get_env("OPENAI_API_KEY"))
        else:
            # Ollama - uses OpenAI-compatible API
            ollama_url = get_env("OLLAMA_BASE_URL", "http://localhost:11434")
            return OpenAI(
                api_key="ollama",  # Ollama doesn't need a real key
                base_url=f"{ollama_url}/v1",
            )
    
    def _clean_json_string(self, s: str) -> str:
        """Remove control characters and fix common JSON issues."""
        import re
        # Remove control characters (except newlines and tabs which we'll handle)
        s = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', s)
        # Replace literal newlines inside strings with escaped versions
        # This is a simplified approach - find JSON string values and escape newlines
        result = []
        in_string = False
        escape_next = False
        for char in s:
            if escape_next:
                result.append(char)
                escape_next = False
                continue
            if char == '\\':
                result.append(char)
                escape_next = True
                continue
            if char == '"':
                in_string = not in_string
                result.append(char)
                continue
            if in_string and char == '\n':
                result.append('\\n')
                continue
            if in_string and char == '\t':
                result.append('\\t')
                continue
            result.append(char)
        return ''.join(result)
    
    def chat(self, messages: list[dict], session_history: list[dict]) -> dict:
        """Send a chat completion request."""
        start_time = time.time()
        
        full_messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *session_history,
            *messages,
        ]
        
        try:
            # Ollama may not support response_format, so handle differently
            kwargs = {
                "model": self.model,
                "messages": full_messages,
                "temperature": 0,
            }
            
            # Only add response_format for OpenAI/Azure (Ollama may not support it)
            if self.provider in ("openai", "azure"):
                kwargs["response_format"] = {"type": "json_object"}
            
            response = self.client.chat.completions.create(**kwargs)
            
            latency_ms = int((time.time() - start_time) * 1000)
            content = response.choices[0].message.content
            
            # Handle token usage first (Ollama may not provide all fields)
            usage = response.usage
            token_usage = {
                "prompt_tokens": getattr(usage, "prompt_tokens", 0) or 0,
                "completion_tokens": getattr(usage, "completion_tokens", 0) or 0,
                "total_tokens": getattr(usage, "total_tokens", 0) or 0,
            }
            
            # Parse JSON response (handle markdown code blocks and control chars from Ollama)
            content = content.strip()
            
            # Remove markdown code blocks
            if content.startswith("```"):
                lines = content.split("\n")
                # Remove first line (```json) and last line (```)
                if lines[-1].strip().startswith("```"):
                    lines = lines[1:-1]
                else:
                    lines = lines[1:]
                content = "\n".join(lines)
            
            # Clean control characters that break JSON parsing
            content = self._clean_json_string(content)
            
            parsed = json.loads(content)
            
            return {
                "natural_language_answer": parsed.get("answer", ""),
                "sql_query": parsed.get("sql_query", ""),
                "token_usage": token_usage,
                "latency_ms": latency_ms,
                "provider": self.provider,
                "model": self.model,
                "status": "ok",
            }
        except json.JSONDecodeError as e:
            latency_ms = int((time.time() - start_time) * 1000)
            # Try to extract answer and sql_query using regex as fallback
            answer = ""
            sql_query = ""
            raw_content = content if 'content' in locals() else ""
            if raw_content:
                import re
                # Try to find "answer": "..." pattern
                answer_match = re.search(r'"answer"\s*:\s*"([^"]*(?:\\.[^"]*)*)"', raw_content, re.DOTALL)
                if answer_match:
                    answer = answer_match.group(1).replace('\\n', '\n').replace('\\"', '"')
                # Try to find "sql_query": "..." pattern  
                sql_match = re.search(r'"sql_query"\s*:\s*"([^"]*(?:\\.[^"]*)*)"', raw_content, re.DOTALL)
                if sql_match:
                    sql_query = sql_match.group(1).replace('\\n', '\n').replace('\\"', '"')
            
            if answer:  # If we extracted something, return it as success
                return {
                    "natural_language_answer": answer,
                    "sql_query": sql_query,
                    "token_usage": token_usage if 'token_usage' in locals() else {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                    "latency_ms": latency_ms,
                    "provider": self.provider,
                    "model": self.model,
                    "status": "ok",
                }
            
            return {
                "natural_language_answer": raw_content or "Failed to parse response",
                "sql_query": "",
                "token_usage": token_usage if 'token_usage' in locals() else {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "latency_ms": latency_ms,
                "provider": self.provider,
                "model": self.model,
                "status": "error",
                "error_message": f"JSON parse error: {str(e)}",
            }
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "natural_language_answer": "",
                "sql_query": "",
                "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "latency_ms": latency_ms,
                "provider": self.provider,
                "model": self.model,
                "status": "error",
                "error_message": str(e),
            }
