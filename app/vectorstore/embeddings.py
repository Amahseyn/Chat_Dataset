from langchain_google_genai import GoogleGenerativeAIEmbeddings
from core.config import get_settings

def get_embeddings():
    return GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=get_settings().GOOGLE_API_KEY
    )