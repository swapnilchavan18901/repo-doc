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
    print(f"\n{'='*60}")
    print(f"🎯 WEBHOOK RECEIVED")
    print(f"{'='*60}\n")
    
    try:
        # Parse GitHub webhook payload
        payload = await request.json()
        print(f"📦 Payload received: {json.dumps(payload, indent=2)[:500]}...")
        
        # Extract repository and commit information
        repo_full_name = payload.get("repository", {}).get("full_name")
        before_sha = payload.get("before")
        after_sha = payload.get("after")
        
        print(f"📊 Extracted data:")
        print(f"   - Repository: {repo_full_name}")
        print(f"   - Before SHA: {before_sha}")
        print(f"   - After SHA: {after_sha}")
        print(f"   - Database ID: {NOTION_DATABASE_ID}")
        
        if not repo_full_name or not before_sha or not after_sha:
            error_msg = "Missing required fields: repository.full_name, before, or after"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
        
        print(f"\n🚀 Starting agent execution...")
        
        # Pass repo context to AI agent - it will find/create the right page
        result = await generate_notion_docs(
                 repo_full_name=repo_full_name,
                 before_sha=before_sha,
                 after_sha=after_sha,
                 database_id=NOTION_DATABASE_ID
                )

        print(f"📋 Result: {result}")
        
        return {
            "success": True,
            "data": result,
            "repo": repo_full_name,
            "commits": f"{before_sha[:7]}...{after_sha[:7]}"
        }
    except Exception as e:
        error_msg = f"Error in webhook: {str(e)}"
        print(f"❌ {error_msg}")
        import traceback
        print(f"🔍 Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "error": error_msg,
            "traceback": traceback.format_exc()
        }