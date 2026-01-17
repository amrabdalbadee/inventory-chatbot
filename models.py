"""Pydantic models for API request/response validation."""
from typing import Optional, Any, Literal
from pydantic import BaseModel


class ChatRequest(BaseModel):
    session_id: str
    message: str
    context: Optional[dict[str, Any]] = None


class TokenUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatResponse(BaseModel):
    natural_language_answer: str
    sql_query: str
    token_usage: TokenUsage
    latency_ms: int
    provider: Literal["openai", "azure", "ollama"]
    model: str
    status: Literal["ok", "error"]
    error_message: Optional[str] = None
