import json
import os
from litellm import completion
from services.notion import NotionService
from services.github_actions import GitHubService
from env import LLM_API_KEY
from prompts.generate_notion_prompt import get_notion_prompt

os.environ["OPENAI_API_KEY"] = LLM_API_KEY
DEFAULT_MAX_ITERATIONS = 100
github_service = GitHubService()
notion_service = NotionService()

def call_llm_streaming(messages):
    try:
        response = completion(
            model="gpt-4.1",
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

    return {
        "content": parsed_response.get("content"),
        "iterations": iteration_count
    }

if __name__ == "__main__":
    # You can specify database_id for new page or page_id for existing page
    # Example: generate_notion_docs(database_id="your-database-id")
    # Example: generate_notion_docs(page_id="your-existing-page-id")
    generate_notion_docs()