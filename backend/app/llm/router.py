"""LLM router - re-exports the chat router from routes."""

from app.routes.chat import router

__all__ = ["router"]
