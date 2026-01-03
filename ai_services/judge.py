import json
import os
from litellm import completion
from services.notion import NotionService
from env import LLM_API_KEY
from prompts.judge_prompt import get_judge_prompt

os.environ["OPENAI_API_KEY"] = LLM_API_KEY

DEFAULT_MAX_ITERATIONS = 50
notion_service = NotionService()

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
    "get_notion_page_content": notion_service.get_page_content,
    "update_notion_section": notion_service.replace_section,
    "append_notion_blocks": notion_service.append_blocks,
    "create_notion_blocks": notion_service.create_blocks,
    "add_block_to_page": notion_service.add_block_to_page,
    "insert_blocks_after_text": notion_service.insert_between_by_text,
    "insert_blocks_after_block_id": notion_service.insert_after_block,
}

def judge_notion_docs(
    page_id: str,
    generation_context: str = None,
    max_iterations: int = DEFAULT_MAX_ITERATIONS
):
    """
    Review and assess the quality of Notion documentation.
    
    Args:
        page_id: The Notion page ID to review
        generation_context: Context from the documentation generation process
        max_iterations: Maximum number of iterations for the review process
        
    Returns:
        dict: Quality report with status, score, issues, and recommendations
    """
    
    if not page_id:
        return {
            "status": "error",
            "content": "No page_id provided for review"
        }
    
    context_info = ""
    
    # Add generation context if provided
    if generation_context:
        context_info += generation_context
        context_info += "\n"
    
    # Add Notion page context
    context_info += f"TARGET PAGE ID: {page_id}\n"
    context_info += f"\nTo retrieve content, use: get_notion_page_content('{page_id}')\n"
    context_info += f"To update sections, use: update_notion_section('{page_id}|section_identifier|new_content')\n"
    context_info += f"To append blocks, use: append_notion_blocks('{page_id}|blocks_json')\n"
    
    print(f"\n{'='*60}")
    print(f"📋 STARTING DOCUMENTATION QUALITY REVIEW")
    print(f"{'='*60}")
    print(f"Page ID: {page_id}")
    print(f"{'='*60}\n")
    
    system_prompt = get_judge_prompt(context_info)
    
    messages = [
        {"role": "system", "content": system_prompt},
    ]
    
    iteration_count = 0
    
    while iteration_count < max_iterations:
        iteration_count += 1
        print(f"\n{'='*60}")
        print(f"🔄 Review Iteration {iteration_count}/{max_iterations}")
        print(f"{'='*60}\n")
        
        try:
            full_content = call_llm_streaming(messages)
            print(f"✅ Received {len(full_content)} characters from Judge LLM")
            
            print(f"\n{'='*60}")
            print("JUDGE OUTPUT:")
            print(f"{'='*60}")
            print(full_content)
            print(f"{'='*60}\n")
        except Exception as e:
            print(f"❌ Error during Judge LLM call: {e}")
            return {
                "status": "error",
                "content": f"Judge LLM error: {str(e)}",
                "iterations": iteration_count
            }
        
        try:
            parsed_response = json.loads(full_content)
            print(f"📋 Judge Response: {json.dumps(parsed_response, indent=2)}")
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse Judge response as JSON: {e}")
            return {
                "status": "error",
                "content": "Invalid JSON response from Judge",
                "iterations": iteration_count
            }
        
        messages.append({"role": "assistant", "content": full_content})

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

