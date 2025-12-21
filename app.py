import json
import os
import subprocess
from openai import OpenAI
from dotenv import load_dotenv
from routes import base, examples, dinkachika
from fastapi import APIRouter, FastAPI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_app() -> FastAPI:
    """Creates and returns FastAPI app with routes attached"""
    app = FastAPI()

    # Add base route at localhost:8000
    app.include_router(base.router)
    app.include_router(dinkachika.router)

    # Add additional routes under localhost:8000/api
    app.include_router(get_router(), prefix="/api")
    return app

def get_router() -> APIRouter:
    """Creates router that will contain additional routes under localhost:8000/api"""
    router = APIRouter()

    # Example route
    router.include_router(examples.router, prefix="/example")
    return router

app = get_app()

def add (a: int, b: int):
    return a + b

def subtract (a: int, b: int):
    return a - b

def multiply (a: int, b: int):
    return a * b

def check_git_status(input: str = ""):
        status = subprocess.check_output(["git", "status"], text=True)
        diff = subprocess.check_output(["git", "diff"], text=True)
        return {
            "git_status": status,
            "git_change_content": diff
        }

def run_command(cmd: str):
    """Run a shell command and return both output and exit code"""
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
     
def read_md_file(filename: str):
    """Read content from a markdown file"""
    try:
        if not filename.endswith('.md'):
            filename += '.md'
        with open(filename, 'r', encoding='utf-8') as f:
            return {"success": True, "content": f.read(), "filename": filename}
    except FileNotFoundError:
        return {"success": False, "error": f"File {filename} not found", "filename": filename}
    except Exception as e:
        return {"success": False, "error": str(e), "filename": filename}

def write_md_file(input_str: str):
    """Create or overwrite a markdown file. Input format: 'filename.md|content'"""
    try:
        # Split on first | to separate filename and content
        if '|' not in input_str:
            return {"success": False, "error": "Input must be in format 'filename.md|content'", "input": input_str}

        filename, content = input_str.split('|', 1)

        # Clean up filename
        filename = filename.strip()
        if not filename.endswith('.md'):
            filename += '.md'

        # Write the file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)

        return {"success": True, "message": f"File {filename} written successfully", "filename": filename, "content_length": len(content)}
    except Exception as e:
        return {"success": False, "error": str(e), "input": input_str}

def edit_md_file(input_str: str):
    """Edit content in a markdown file. Input format: 'filename.md|old_content|new_content'"""
    try:
        # Split on | to separate filename, old_content, and new_content
        parts = input_str.split('|', 2)
        if len(parts) != 3:
            return {"success": False, "error": "Input must be in format 'filename.md|old_content|new_content'", "input": input_str}

        filename, old_content, new_content = parts

        # Clean up filename
        filename = filename.strip()
        if not filename.endswith('.md'):
            filename += '.md'

        # Read current content
        with open(filename, 'r', encoding='utf-8') as f:
            current_content = f.read()

        # Normalize content for better matching (strip whitespace and normalize line endings)
        def normalize_content(content):
            return content.strip().replace('\r\n', '\n').replace('\r', '\n')

        normalized_old = normalize_content(old_content)
        normalized_current = normalize_content(current_content)

        # Try exact match first
        if old_content in current_content:
            updated_content = current_content.replace(old_content, new_content, 1)
        elif normalized_old in normalized_current:
            # Fallback: try normalized matching
            updated_content = current_content.replace(normalized_old, new_content, 1)
        else:
            # If still no match, provide detailed error with suggestions
            return {
                "success": False,
                "error": "Old content not found in file. This may be due to encoding issues, whitespace differences, or content changes.",
                "filename": filename,
                "suggestion": "Consider using write_md_file to overwrite the entire file instead of edit_md_file for complex edits."
            }

        # Write back
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(updated_content)

        return {"success": True, "message": f"File {filename} updated successfully", "filename": filename}
    except FileNotFoundError:
        return {"success": False, "error": f"File {filename} not found", "input": input_str}
    except Exception as e:
        return {"success": False, "error": str(e), "input": input_str}

def list_md_files(data: str = ""):
    """List all markdown files in the current directory"""
    try:
        md_files = [f for f in os.listdir('.') if f.endswith('.md')]
        return {"success": True, "files": md_files, "count": len(md_files)}
    except Exception as e:
        return {"success": False, "error": str(e)}

available_tools = {
    "check_git_status": check_git_status,
    "run_command": run_command,
    "read_md_file": read_md_file,
    "write_md_file": write_md_file,
    "edit_md_file": edit_md_file,
    "list_md_files": list_md_files,
    "add": add
}
@app.get("/generate_api_overview")
def generate_api_overview():
    with open("README.md", "r") as file:
        readme_content = file.read()
    SYSTEM_PROMPT = f"""
    You are an AI Documentation Agent specialized in generating comprehensive documentation for software projects.
    The README.md file is the main documentation file for the project. You use ONLY Git status and diff information (via the check_git_status function) to understand what the project does and what needs to be documented.
    IMPORTANT: You will NOT scan or read any files other than README.md directly - all project understanding must come from Git status information.

    ## Workflow Process:
    You must follow a strict step-by-step workflow using JSON responses:

    ### Step Types:
    1. **plan**: Analyze what information you need and plan your approach
    2. **action**: Call a tool to gather information
    3. **observe**: Process tool results and plan next steps
    4. **write**: Write comprehensive documentation to .md files using write_md_file tool
    5. **output**: Provide final summary (after files are written)

    ### JSON Response Format:
    {{
        "step": "plan|action|observe|output",
        "content": "Your analysis or plan description",
        "function": "tool_name",  // only for action steps
        "input": "tool_input"      // only for action steps
    }}

    ## Documentation Output Requirements:
    When generating documentation, you MUST:
    1. Create comprehensive, complete documentation that fully describes the project
    2. Use Git status and diff to understand the current state and functionality of the project
    3. Update the README.md file with complete project information, features, API endpoints, usage examples, and technical details
    4. Maintain a professional, well-structured README.md that serves as the single source of truth for the project
    5. Include all necessary sections for a complete project README (features, installation, usage, API docs, etc.)
    6. Focus on creating documentation that helps developers understand and use the project effectively

    ## File Editing Instructions:
    Use the edit_md_file tool to update the README.md file:
    - edit_md_file("README.md|old_content|new_content")
    - Use | to separate filename, old_content, and new_content
    - The tool handles file editing automatically with robust content matching
    - If edit_md_file fails due to content matching issues, use write_md_file as fallback: write_md_file("README.md|complete_new_content")
    - After editing, verify the file was updated by using read_md_file to check the content
    - Always read the current README.md content first to understand what needs to be updated
    - For complex edits, prefer write_md_file over edit_md_file to avoid matching issues

    ## Example Workflow:
    1. Plan: {{ "step": "plan", "content": "Need to analyze the project structure and current functionality" }}
    2. Action: {{ "step": "action", "function": "check_git_status", "input": "" }}
    3. Observe: {{ "step": "observe", "content": "Analyzing project files with check_git_status function and functionality..." }}
    4. Action: {{ "step": "action", "function": "read_md_file", "input": "README.md" }}
    6. Action: {{ "step": "action", "function": "edit_md_file", "input": "README.md|current_content|comprehensive_updated_content" }}
    7. Output: {{ "step": "output", "content": "Comprehensive README.md documentation generated successfully" }}

    Always be thorough, accurate, and focus on creating documentation that provides complete understanding of the project rather than just summarizing recent changes.
    """
    messages = [
            { "role": "system", "content": SYSTEM_PROMPT },
    ]
    while True:
        response = client.chat.completions.create(
            model="gpt-4.1",
            response_format={"type": "json_object"},
            messages=messages
        )

        messages.append({ "role": "assistant", "content": response.choices[0].message.content })

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

    return {"content": parsed_response.get("content")}

