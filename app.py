import json
import os
import subprocess
from dotenv import load_dotenv
from fastapi import FastAPI, Request
# from ai_services.generate_notion_docs import generate_notion_docs
from agents_sdk.openai_sdk import generate_notion_docs
from env import NOTION_DATABASE_ID

load_dotenv()


def get_app() -> FastAPI:
    """Creates and returns FastAPI app with routes attached"""
    app = FastAPI()
    return app


app = get_app()

@app.post("/webhook")
async def generate_notion_docs_endpoint(request: Request):

    try:
        # Parse GitHub webhook payload
        payload = await request.json()
        
        # Extract repository and commit information
        repo_full_name = payload.get("repository", {}).get("full_name")
        before_sha = payload.get("before")
        after_sha = payload.get("after")
        
        if not repo_full_name or not before_sha or not after_sha:
            return {
                "success": False,
                "error": "Missing required fields: repository.full_name, before, or after"
            }
        
        # Pass repo context to AI agent - it will find/create the right page
        # result = generate_notion_docs(
        #     repo_full_name=repo_full_name,
        #     before_sha=before_sha,
        #     after_sha=after_sha
        # )
        result = generate_notion_docs(
                 repo_full_name=repo_full_name,
                 before_sha=before_sha,
                 after_sha=after_sha
                 NOTION_DATABASE_ID
                )

        
        return {
            "success": True,
            "data": result,
            "repo": repo_full_name,
            "commits": f"{before_sha[:7]}...{after_sha[:7]}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }