import json
import os
import subprocess
import re
from openai import OpenAI
# Notion-specific tools
from services.notion import NotionService
from env import OPENAI_API_KEY
# Import prompt
from prompts.generate_notion_prompt import get_notion_prompt

client = OpenAI(api_key=OPENAI_API_KEY)
DEFAULT_MAX_ITERATIONS = 50

ALLOWED_COMMANDS = [
    # Git commands
    r'^git\s+(status|diff|log|show|branch|remote|config\s+--get)',
    # File/directory operations (read-only)
    r'^ls(\s|$)',
    r'^cat\s+',
    r'^head\s+',
    r'^tail\s+',
    r'^find\s+',
    r'^grep\s+',
    r'^tree(\s|$)',
    r'^pwd(\s|$)',
    r'^which\s+',
    # Python operations
    r'^python\s+-m\s+',
    r'^pip\s+(list|show|freeze)(\s|$)',
    # Node/npm operations (read-only)
    r'^npm\s+(list|view|info)(\s|$)',
    r'^node\s+--version(\s|$)',
    # System info (read-only)
    r'^echo\s+',
    r'^whoami(\s|$)',
    r'^date(\s|$)',
    r'^uname(\s|$)',
]
BLOCKED_PATTERNS = [
    r'rm\s+-rf',  # Recursive force delete
    r'rm\s+.*\*',  # Wildcard delete
    r'dd\s+',  # Disk operations
    r'mkfs',  # Format filesystem
    r'>\s*/dev/',  # Write to device files
    r'sudo\s+',  # Elevated privileges
    r'su\s+',  # Switch user
    r'chmod\s+777',  # Insecure permissions
    r'curl.*\|\s*bash',  # Pipe to shell
    r'wget.*\|\s*sh',  # Pipe to shell
    r'eval\s+',  # Code evaluation
    r'exec\s+',  # Execute
    r':\(\)\{.*\}',  # Fork bomb
    r'mv\s+/',  # Move system directories
    r'cp\s+.*>\s*/',  # Overwrite system files
]

def is_command_safe(cmd: str) -> tuple[bool, str]:
    """
    Validate if a command is safe to execute.
    Returns (is_safe, reason)
    """
    cmd = cmd.strip()
    
    # Check for empty command
    if not cmd:
        return False, "Empty command"
    
    # Check against blocked patterns first
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            return False, f"Blocked: Command matches dangerous pattern '{pattern}'"
    
    # Check if command matches any allowed pattern
    for pattern in ALLOWED_COMMANDS:
        if re.match(pattern, cmd):
            return True, "Command allowed"
    
    return False, f"Command not in whitelist. For security, only specific commands are allowed."
def check_git_status(input: str = ""):
        status = subprocess.check_output(["git", "status"], text=True)
        diff = subprocess.check_output(["git", "diff"], text=True)
        return {
            "git_status": status,
            "git_change_content": diff
        }

def run_command(cmd: str):
    """Run a shell command with security validation and return both output and exit code"""
    # Security check before execution
    is_safe, reason = is_command_safe(cmd)
    
    if not is_safe:
        return {
            "success": False,
            "error": f"SECURITY BLOCK: {reason}",
            "command": cmd,
            "blocked": True
        }
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": cmd
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Command timed out after 30 seconds",
            "command": cmd
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "command": cmd
        }  
 

def get_notion_databases(input_str: str = ""):
    """Get all available Notion databases"""
    try:
        notion = NotionService()
        result = notion.get_all_databases()
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_notion_page_content(page_id: str):
    """Get content from a Notion page with block structure"""
    try:
        notion = NotionService()
        blocks = notion.get_page_blocks(page_id)
        
        # Convert blocks to readable format with section numbers
        content_sections = []
        section_count = 0
        
        for i, block in enumerate(blocks):
            block_type = block["type"]
            
            if block_type.startswith("heading"):
                section_count += 1
                text = notion._get_block_text(block)
                content_sections.append({
                    "section": section_count,
                    "type": block_type,
                    "text": text,
                    "block_id": block["id"]
                })
            elif block_type in ["paragraph", "bulleted_list_item", "numbered_list_item"]:
                text = notion._get_block_text(block)
                if text.strip():  # Only include non-empty content
                    content_sections.append({
                        "section": section_count,
                        "type": block_type,
                        "text": text,
                        "block_id": block["id"]
                    })
        
        return {
            "success": True,
            "page_id": page_id,
            "sections": content_sections,
            "total_sections": section_count,
            "note": "Content organized by sections for easy section-based editing"
        }
    except Exception as e:
        return {"success": False, "error": str(e), "page_id": page_id}

def create_notion_doc_page(input_str: str):
    """Create a new documentation page in Notion. Format: 'database_id|page_title'"""
    try:
        if '|' not in input_str:
            return {"success": False, "error": "Input must be in format 'database_id|page_title'"}
        
        database_id, title = input_str.split('|', 1)
        database_id = database_id.strip()
        title = title.strip()
        
        notion = NotionService()
        result = notion.create_doc_page(database_id, title)
        return result
    except Exception as e:
        return {"success": False, "error": str(e), "input": input_str}

def update_notion_section(input_str: str):
    """Update a specific section in Notion page. Format: 'page_id|heading_text|content_blocks_json'"""
    try:
        parts = input_str.split('|', 2)
        if len(parts) != 3:
            return {"success": False, "error": "Input must be in format 'page_id|heading_text|content_blocks_json'"}
        
        page_id, heading_text, content_json = parts
        page_id = page_id.strip()
        heading_text = heading_text.strip()
        
        # Parse content blocks from JSON
        try:
            import json
            content_blocks = json.loads(content_json)
        except json.JSONDecodeError:
            return {"success": False, "error": "Invalid JSON format for content blocks"}
        
        notion = NotionService()
        result = notion.replace_section(page_id, heading_text, content_blocks)
        return result
    except Exception as e:
        return {"success": False, "error": str(e), "input": input_str}

def append_notion_blocks(input_str: str):
    """Append blocks to a Notion page. Format: 'page_id|blocks_json'"""
    try:
        if '|' not in input_str:
            return {"success": False, "error": "Input must be in format 'page_id|blocks_json'"}
        
        page_id, blocks_json = input_str.split('|', 1)
        page_id = page_id.strip()
        
        # Parse blocks from JSON
        try:
            import json
            blocks = json.loads(blocks_json)
        except json.JSONDecodeError:
            return {"success": False, "error": "Invalid JSON format for blocks"}
        
        notion = NotionService()
        result = notion.append_blocks(page_id, blocks)
        return result
    except Exception as e:
        return {"success": False, "error": str(e), "input": input_str}

def create_notion_blocks(input_str: str):
    """Helper to create Notion blocks from text. Format: 'block_type|text' or 'block_type|text|extra_param'"""
    try:
        notion = NotionService()
        
        if '|' not in input_str:
            return {"success": False, "error": "Input must be in format 'block_type|text' or 'block_type|text|extra_param'"}
        
        parts = input_str.split('|')
        block_type = parts[0].strip().lower()
        
        # Basic blocks (single text parameter)
        if block_type == "h1":
            block = notion.h1(parts[1].strip())
        elif block_type == "h2":
            block = notion.h2(parts[1].strip())
        elif block_type == "h3":
            block = notion.h3(parts[1].strip())
        elif block_type == "paragraph":
            block = notion.paragraph(parts[1].strip())
        elif block_type == "bullet":
            block = notion.bullet(parts[1].strip())
        elif block_type == "numbered":
            block = notion.numbered(parts[1].strip())
        elif block_type == "quote":
            block = notion.quote(parts[1].strip())
        
        # Code blocks (requires language parameter)
        elif block_type == "code":
            code_content = parts[1].strip()
            language = parts[2].strip() if len(parts) > 2 else "python"
            block = notion.code(code_content, language)
        
        # Callout blocks (optional emoji parameter)
        elif block_type == "callout":
            text = parts[1].strip()
            emoji = parts[2].strip() if len(parts) > 2 else "💡"
            block = notion.callout(text, emoji)
        
        # To-do blocks (optional checked parameter)
        elif block_type == "todo" or block_type == "to_do":
            text = parts[1].strip()
            checked = parts[2].strip().lower() == "true" if len(parts) > 2 else False
            block = notion.to_do(text, checked)
        
        # Toggle blocks (with optional children)
        elif block_type == "toggle":
            summary = parts[1].strip()
            children = None
            if len(parts) > 2:
                try:
                    children = json.loads(parts[2])
                except json.JSONDecodeError:
                    return {"success": False, "error": "Invalid JSON for toggle children"}
            block = notion.toggle(summary, children)
        
        # Special blocks (no parameters)
        elif block_type == "divider":
            block = notion.divider()
        elif block_type == "toc" or block_type == "table_of_contents":
            block = notion.table_of_contents()
        
        # Mixed/complex blocks (JSON input)
        elif block_type == "mixed":
            try:
                return {"success": True, "blocks": json.loads(parts[1])}
            except json.JSONDecodeError:
                return {"success": False, "error": "Invalid JSON for mixed blocks"}
        
        else:
            return {"success": False, "error": f"Unsupported block type: {block_type}. Supported types: h1, h2, h3, paragraph, bullet, numbered, code, quote, callout, divider, toggle, todo, toc, mixed"}
        
        return {"success": True, "block": block}
    except Exception as e:
        return {"success": False, "error": str(e), "input": input_str}

def insert_blocks_after_text(input_str: str):
    """Insert blocks after a block with specific text. Format: 'page_id|after_text|blocks_json'"""
    try:
        parts = input_str.split('|', 2)
        if len(parts) != 3:
            return {"success": False, "error": "Input must be in format 'page_id|after_text|blocks_json'"}
        
        page_id, after_text, blocks_json = parts
        page_id = page_id.strip()
        after_text = after_text.strip()
        
        # Parse blocks from JSON
        try:
            import json
            blocks = json.loads(blocks_json)
        except json.JSONDecodeError:
            return {"success": False, "error": "Invalid JSON format for blocks"}
        
        notion = NotionService()
        result = notion.insert_between_by_text(page_id, after_text, blocks)
        return result
    except Exception as e:
        return {"success": False, "error": str(e), "input": input_str}

def insert_blocks_after_block_id(input_str: str):
    """Insert blocks after a specific block ID. Format: 'block_id|blocks_json'"""
    try:
        if '|' not in input_str:
            return {"success": False, "error": "Input must be in format 'block_id|blocks_json'"}
        
        block_id, blocks_json = input_str.split('|', 1)
        block_id = block_id.strip()
        
        # Parse blocks from JSON
        try:
            import json
            blocks = json.loads(blocks_json)
        except json.JSONDecodeError:
            return {"success": False, "error": "Invalid JSON format for blocks"}
        
        notion = NotionService()
        result = notion.insert_after_block(block_id, blocks)
        return result
    except Exception as e:
        return {"success": False, "error": str(e), "input": input_str}

# Remove markdown file functions - replaced with Notion functions above

def read_file(filename: str):
    """Read content from any file in the project structure"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return {"success": True, "content": f.read(), "filename": filename}
    except FileNotFoundError:
        return {"success": False, "error": f"File {filename} not found", "filename": filename}
    except UnicodeDecodeError:
        return {"success": False, "error": f"File {filename} cannot be decoded as UTF-8 text", "filename": filename}
    except Exception as e:
        return {"success": False, "error": str(e), "filename": filename}


available_tools = {
    "check_git_status": check_git_status,
    "run_command": run_command,
    "read_file": read_file,
    "get_notion_databases": get_notion_databases,
    "get_notion_page_content": get_notion_page_content,
    "create_notion_doc_page": create_notion_doc_page,
    "update_notion_section": update_notion_section,
    "append_notion_blocks": append_notion_blocks,
    "create_notion_blocks": create_notion_blocks,
    "insert_blocks_after_text": insert_blocks_after_text,
    "insert_blocks_after_block_id": insert_blocks_after_block_id,
}

def generate_notion_docs(database_id: str = None, page_id: str = None, max_iterations: int = DEFAULT_MAX_ITERATIONS):    
    context_info = ""
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
        
        response = client.chat.completions.create(
            model="gpt-5-nano",
            response_format={"type": "json_object"},
            messages=messages
        )

        messages.append({ "role": "assistant", "content": response.choices[0].message.content })
        print(response.choices[0].message.content)
        try:
            parsed_response = json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            print(f"❌: Failed to parse JSON response: {response.choices[0].message.content}")
            break

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