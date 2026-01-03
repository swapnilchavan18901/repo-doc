import json
import os
from litellm import completion
from services.notion import NotionService
from services.github_actions import GitHubService
from env import LLM_API_KEY
from prompts.generate_notion_prompt import get_notion_prompt
from ai_services.judge import judge_notion_docs
os.environ["OPENAI_API_KEY"] = LLM_API_KEY
DEFAULT_MAX_ITERATIONS = 100
github_service = GitHubService()
notion_service = NotionService()

def get_latest_page_from_database(database_id):
    """
    Query the database to get the most recently created page.
    
    Args:
        database_id: The Notion database ID
        
    Returns:
        str: Page ID if found, None otherwise
    """
    if not database_id:
        return None
    
    try:
        # Query database for pages, sorted by creation time (most recent first)
        result = notion_service.query_database_pages(f"{database_id}|1")
        
        if result.get("success") and result.get("pages"):
            page = result["pages"][0]  # Get the most recent page
            page_id = page.get("page_id")
            print(f"📍 Found most recent page in database: {page_id}")
            print(f"   Title: {page.get('title')}")
            print(f"   Created: {page.get('created_time')}")
            return page_id
        else:
            print(f"⚠️ No pages found in database {database_id}")
            return None
            
    except Exception as e:
        print(f"❌ Error querying database: {e}")
        return None

def call_llm_streaming(messages):
    try:
        response = completion(
            model="gpt-5-nano",
            messages=messages,
        )
        
        full_content = response.choices[0].message.content
        
        if not full_content or not full_content.strip():
            raise Exception("Received empty response from LLM")
        
        return full_content
    except Exception as e:
        raise Exception(f"LLM API Error: {e}")

available_tools = {
    "get_github_diff": github_service.get_diff,
    "get_github_file_tree": github_service.get_file_tree,
    "read_github_file": github_service.read_file,
    "search_github_code": github_service.search_code,
    "list_all_github_files": github_service.list_all_files_recursive,
    "get_notion_databases": notion_service.get_all_databases,
    "search_page_by_title": notion_service.search_page_by_title,
    "get_notion_page_content": notion_service.get_page_content,
    "create_notion_doc_page": notion_service.create_doc_page,
    "update_notion_section": notion_service.replace_section,
    "append_notion_blocks": notion_service.append_blocks,
    "create_notion_blocks": notion_service.create_blocks,
    "add_block_to_page": notion_service.add_block_to_page,
    "insert_blocks_after_text": notion_service.insert_between_by_text,
    "insert_blocks_after_block_id": notion_service.insert_after_block,
}

def generate_notion_docs(
    repo_full_name: str = None,
    before_sha: str = None,
    after_sha: str = None,
    database_id: str = None,
    page_id: str = None,
    max_iterations: int = DEFAULT_MAX_ITERATIONS
):    
    context_info = ""
    
    # Add GitHub repository context
    if repo_full_name and before_sha and after_sha:
        context_info += f"GITHUB REPOSITORY: {repo_full_name}\n"
        context_info += f"COMMIT RANGE: {before_sha[:7]}...{after_sha[:7]}\n"
        context_info += f"\nTo get the diff, use: get_github_diff('{repo_full_name}|{before_sha}|{after_sha}')\n"
        context_info += f"To read files, use: read_github_file('{repo_full_name}|<filepath>|{after_sha}')\n"
        context_info += f"To list files, use: list_all_github_files('{repo_full_name}|{after_sha}')\n\n"
    
    # Add Notion target context
    if database_id:
        context_info += f"TARGET DATABASE ID: {database_id} (create new page)\n"
    if page_id:
        context_info += f"TARGET PAGE ID: {page_id} (update existing page)\n"
    if not database_id and not page_id:
        context_info += "NO TARGET SPECIFIED: You must first discover available databases and either create a new page or identify an existing page to update.\n"

    # Get system prompt from external file
    system_prompt = get_notion_prompt(context_info)
    
    messages = [
            { "role": "system", "content": system_prompt },
    ]
    
    iteration_count = 0
    while iteration_count < max_iterations:
        iteration_count += 1
        print(f"\n{'='*60}")
        print(f"🔄 Iteration {iteration_count}/{max_iterations}")
        print(f"{'='*60}\n")

        try:
            full_content = call_llm_streaming(messages)
            print(f"✅ Received {len(full_content)} characters from LLM")
            print(f"\n{'='*60}")
            print("RAW LLM OUTPUT (for debugging):")
            print(f"{'='*60}")
            print(full_content)
            print(f"{'='*60}\n")
        except Exception as e:
            print(f"❌ Error during LLM call: {e}")
            break

        parsed_response = json.loads(full_content)
        print(f"📋 LLM Response: {json.dumps(parsed_response, indent=2)}")
        
        messages.append({ "role": "assistant", "content": full_content })


        step = parsed_response.get("step")

        if step == "plan":
            print(f"🧠: {parsed_response.get('content')}")
            continue

        elif step == "action":
            tool_name = parsed_response.get("function")
            tool_input = parsed_response.get("input", "")

            print(f"🛠️: Calling Tool: {tool_name} with input '{tool_input}'")
            if tool_name in available_tools:
                try:
                    output = available_tools[tool_name](tool_input)
                    messages.append({
                        "role": "user",
                        "content": json.dumps({
                            "step": "observe",
                            "output": output
                        })
                    })
                except Exception as e:
                    print(f"❌: Tool execution failed: {e}")
                    break
            else:
                print(f"❌: Unknown tool: {tool_name}")
                break
            continue
        elif step == "observe":
            print(f"👁️: {parsed_response.get('content')}")
            continue

        elif step == "write":
            print(f"📝: {parsed_response.get('content')}")
            continue

        elif step == "output":
            print(f"🤖: {parsed_response.get('content')}")
            break

        else:
            print(f"❌: Unknown step: {step}")
            break
    
    # Check if loop ended due to max iterations
    if iteration_count >= max_iterations:
        print(f"\n⚠️  WARNING: Reached maximum iteration limit ({max_iterations})")
        print(f"    The agent loop was terminated to prevent runaway execution.")
        print(f"    If you need more iterations, increase max_iterations parameter.")
        return {
            "content": "Max iterations reached",
            "warning": f"Agent stopped after {max_iterations} iterations",
            "iterations": iteration_count
        }

    result = {
        "content": parsed_response.get("content"),
        "iterations": iteration_count
    }
    # Try to find the created page if not provided
    review_page_id = page_id
    if not review_page_id and database_id:
        # Query database to get the most recently created page
        review_page_id = get_latest_page_from_database(database_id)
    
    # Run quality review if we have a page_id (either provided or extracted)
    if review_page_id:
        print(f"\n{'='*60}")
        print(f"🔍 INITIATING QUALITY REVIEW")
        print(f"{'='*60}\n")
        
        try:
            # Build context summary for judge
            judge_context = f"GENERATED DOCUMENTATION SUMMARY:\n"
            judge_context += f"- Page ID: {review_page_id}\n"
            judge_context += f"- Generation iterations: {iteration_count}\n"
            if repo_full_name:
                judge_context += f"- Source: {repo_full_name} ({before_sha[:7]}...{after_sha[:7]})\n"
            judge_context += f"\nDocumentation was just generated/updated. Review and fix quality issues.\n"
            
            judge_result = judge_notion_docs(
                page_id=review_page_id,
                generation_context=judge_context,
                max_iterations=50
            )
            
            result["judge_result"] = judge_result
            result["reviewed_page_id"] = review_page_id
            print(f"\n{'='*60}")
            print(f"✅ QUALITY REVIEW COMPLETED")
            print(f"📊 Judge completed in {judge_result.get('iterations')} iterations")
            print(f"{'='*60}\n")
                
        except Exception as e:
            print(f"\n❌ Quality review failed: {e}")
            result["judge_error"] = str(e)
    else:
        print(f"\n⚠️  Quality review skipped: No page_id available")
        result["judge_skipped"] = "No page_id found for review"

    return result
