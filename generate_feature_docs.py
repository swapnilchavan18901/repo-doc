import json
import os
import subprocess
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
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
    "read_md_file": read_md_file,
    "read_file": read_file,
    "write_md_file": write_md_file,
    "edit_md_file": edit_md_file,
    "list_md_files": list_md_files,
}
def generate_feature_docs():
    with open("FEATUREREADME.md", "r") as file:
        readme_content = file.read()
    SYSTEM_PROMPT = f"""
    You are an AI Documentation Agent specialized in generating comprehensive, feature-focused documentation for software projects.
    You can read any file in the project structure to understand features, functionality, and implementation details.
    Your primary goal is to create detailed, feature-level documentation that helps developers understand and use each capability effectively.

    ## Workflow Process:
    You must follow a strict step-by-step workflow using JSON responses:

    ### Step Types:
    1. **plan**: Analyze what information you need and plan your approach to feature documentation
    2. **action**: Call a tool to gather information OR write documentation to files
    3. **observe**: Process tool results and analyze specific features and capabilities
    4. **output**: Provide final summary (after documentation is written)

    ### JSON Response Format:
    {{
        "step": "plan|action|observe|write|output",
        "content": "Your analysis or plan description",
        "function": "tool_name",  // only for action steps
        "input": "tool_input"      // only for action steps
    }}

    ## Feature-Focused Documentation Requirements:
    When generating documentation, you MUST:

    ### 1. **Feature Discovery & Analysis**
    - Read and analyze all relevant source code files to understand features
    - Identify core functionality, APIs, services, and user-facing capabilities
    - Map out the complete feature set and how components interact
    - Understand configuration options, dependencies, and setup requirements

    ### 2. **Detailed Feature Documentation**
    - Document each major feature with clear descriptions, usage examples, and technical details
    - Include API endpoints, parameters, request/response formats, and error handling
    - Explain configuration options and environment variables
    - Provide code examples for each feature implementation
    - Document any CLI commands, scripts, or tools included

    ### 3. **Developer Experience Focus**
    - Create documentation that helps developers quickly understand and implement features
    - Include practical examples and common use cases for each feature
    - Document integration patterns and best practices
    - Explain setup, configuration, and deployment procedures

    ### 4. **Comprehensive FEATUREREADME Structure**
    - **Project Overview**: Clear description of what the project does and its main features
    - **Feature Catalog**: Detailed breakdown of each major feature with examples
    - **Quick Start**: Step-by-step setup and basic usage
    - **API Reference**: Complete endpoint documentation with examples
    - **Configuration**: All settings, environment variables, and options
    - **Examples**: Practical code examples for common use cases
    - **Contributing**: Development setup and contribution guidelines

    ## File Reading Strategy:
    - Start by checking git status to identify which files have been changed
    - Read the changed files to understand what features or functionality were modified
    - Analyze route definitions, service implementations, and model structures in changed files
    - Read existing FEATUREREADME.md to understand current feature coverage
    - Focus documentation updates on the specific features that were changed

    ## File Editing Instructions:
    - Use check_git_status() first to identify changed files
    - Use read_file() to examine changed files and understand feature modifications
    - Use write_md_file for creating/updating the FEATUREREADME.md file
    - Use edit_md_file for updating existing documentation files
    - Prefer write_md_file for major documentation updates to avoid matching issues
    - Always target FEATUREREADME.md as the main documentation file, not README.md
    - IMPORTANT: When writing documentation, you MUST call write_md_file with the COMPLETE documentation content, not just a placeholder
    - Generate comprehensive, detailed documentation content that covers all features found in the analysis
    - Do NOT skip to "output" step until you have actually written the documentation to the file

    ## Example Workflow for Feature Documentation:
    1. Plan: {{ "step": "plan", "content": "Need to analyze changed files to understand what features were modified" }}
    2. Action: {{ "step": "action", "function": "check_git_status", "input": "" }}
    3. Observe: {{ "step": "observe", "content": "Analyzing git status to identify changed files and their modifications..." }}
    4. Action: {{ "step": "action", "function": "read_file", "input": "app.py" }}
    5. Action: {{ "step": "action", "function": "read_file", "input": "routes/base.py" }}
    6. Observe: {{ "step": "observe", "content": "Understanding modified features and API endpoints..." }}
    7. Action: {{ "step": "action", "function": "read_md_file", "input": "FEATUREREADME.md" }}
    8. Write: {{ "step": "write", "content": "FEATUREREADME.md will be updated to document the new /dinkachika/ API route..." }}
    9. Action: {{ "step": "action", "function": "write_md_file", "input": "FEATUREREADME.md|comprehensive_feature_documentation_content_here" }}
    10. Output: {{ "step": "output", "content": "Feature-focused FEATUREREADME.md documentation generated successfully" }}

    IMPORTANT: Only modify FEATUREREADME.md, never README.md. All documentation updates should target FEATUREREADME.md.

    CRITICAL WORKFLOW REMINDER:
    - You MUST call write_md_file with actual documentation content before reaching the "output" step
    - Do NOT provide an "output" response until you have successfully written the documentation to FEATUREREADME.md
    - The workflow should end with actual file changes, not just analysis and planning
    - Generate comprehensive documentation that covers all analyzed features with practical examples

    Focus on creating detailed, practical documentation that makes each feature clear and implementable rather than providing vague overviews.
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

    return {"content": parsed_response.get("content")}

if __name__ == "__main__":
    generate_feature_docs()