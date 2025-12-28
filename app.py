import json
import os
import subprocess
from openai import OpenAI
from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI
from generate_notion_docs import generate_notion_docs

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_app() -> FastAPI:
    """Creates and returns FastAPI app with routes attached"""
    app = FastAPI()
    return app


app = get_app()

@app.post("/webhook")
def generate_notion_docs_endpoint():
    """
    API endpoint to generate Notion documentation.
    
    Args:
        database_id: Optional database ID to create a new page
        page_id: Optional page ID to update an existing page
        max_iterations: Maximum iterations for the agent loop (default: 50)
    
    Returns:
        JSON response with the generated documentation result
    """
    try:
        result = generate_notion_docs()
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }