"""
Single shared LLM client instance. Every agent node imports `llm` from here
instead of creating its own — avoids reinitializing the client repeatedly
and keeps the model name/config in one place.
"""
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings

llm = ChatGoogleGenerativeAI(
    model=settings.GEMINI_MODEL,
    google_api_key=settings.GEMINI_API_KEY,
)
