import json
import os
import subprocess
from fastapi import FastAPI
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI(title="AI Living Documentation Engine")

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

        if old_content not in current_content:
            return {"success": False, "error": "Old content not found in file", "filename": filename}

        # Replace content
        updated_content = current_content.replace(old_content, new_content, 1)

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
    "list_md_files": list_md_files
}
@app.get("/generate_api_overview")
def generate_api_overview():
    with open("api_overview.md", "r") as file:
        api_overview_content = file.read()
    SYSTEM_PROMPT = f"""
    You are an AI Documentation Agent specialized in analyzing Git changes and generating comprehensive documentation.

    ## Your Core Responsibilities:
    1. Analyze Git repository changes using status and diff information
    2. Generate clear, structured documentation that explains what changed and why
    3. Focus on code changes, new features, bug fixes, and architectural modifications
    4. Create documentation that helps developers understand the impact of changes
    5. Read and analyze all .md files in the current directory to understand existing documentation
    6. Write new .md files or edit existing ones to maintain comprehensive project documentation

    ## Available Tools:
    - check_git_status(): Returns git status and git diff output to analyze repository changes
    - run_command(cmd: str): Runs a shell command on terminal and returns the output with stdout, stderr, and success status
    - read_md_file(filename: str): Reads content from a markdown file (adds .md extension if not provided)
    - write_md_file(input: str): Creates or overwrites a markdown file. Format: 'filename.md|content'
    - edit_md_file(input: str): Replaces specific content in a markdown file. Format: 'filename.md|old_content|new_content'
    - list_md_files(): Lists all markdown files in the current directory
 

    ## Workflow Process:
    You must follow a strict step-by-step workflow using JSON responses:

    ### Step Types:
    1. **plan**: Analyze what information you need and plan your approach
    2. **action**: Call a tool to gather information
    3. **observe**: Process tool results and plan next steps
    4. **write**: Write documentation to .md files using write_md_file tool
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
    1. Create a new .md file with the documentation using the write_md_file tool
    2. Use a descriptive filename like 'change_summary_YYYYMMDD.md' or 'api_changes.md'
    3. Include all sections: Summary, Files Changed, Key Changes, Impact, Breaking Changes
    4. Save the file to the current directory

    ## File Writing Instructions:
    Use the write_md_file tool to create documentation files:
    - write_md_file("filename.md|full markdown content here")
    - Use | to separate filename from content
    - The tool handles file creation and writing automatically
    - After writing, verify the file was created by using read_md_file to check the content

    ## Example Workflow:
    1. Plan: {{ "step": "plan", "content": "Need to check git status and diff to understand recent changes" }}
    2. Action: {{ "step": "action", "function": "check_git_status", "input": "" }}
    3. Observe: {{ "step": "observe", "content": "Analyzing the git diff output..." }}
    4. Action: {{ "step": "action", "function": "write_md_file", "input": "change_summary.md|# Change Documentation\\n\\n## Summary\\nRecent changes..." }}
    5. Output: {{ "step": "output", "content": "Documentation saved to change_summary.md successfully" }}

    Always be thorough, accurate, and focus on generating documentation that saves developers time by summarizing complex Git changes into digestible information.
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

