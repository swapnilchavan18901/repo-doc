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
    """Read content from a markdown file WITH LINE NUMBERS for easy line-based editing"""
    try:
        if not filename.endswith('.md'):
            filename += '.md'
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # Create numbered content for easy line identification
        numbered_content = ""
        for i, line in enumerate(lines, start=1):
            numbered_content += f"{i:4d} | {line}"
        
        return {
            "success": True, 
            "content": numbered_content,
            "raw_content": ''.join(lines),
            "filename": filename,
            "total_lines": len(lines),
            "note": "Content includes line numbers (LINE | CONTENT) for easy line-based editing with edit_md_file"
        }
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
    """
    Edit content in a markdown file using line-based replacement for efficiency.
    
    Input formats:
    1. Line-based (preferred): 'filename.md|start_line|end_line|new_content'
       - Replaces lines from start_line to end_line (inclusive, 1-indexed)
       - More efficient, only modifies specific lines
       
    2. Content-based (legacy): 'filename.md|old_content|new_content'
       - Falls back to full file read/write with string replacement
       - Use when you don't know exact line numbers
    """
    try:
        # Split on | to separate components
        parts = input_str.split('|', 3)
        if len(parts) < 3:
            return {"success": False, "error": "Input must be in format 'filename.md|start_line|end_line|new_content' or 'filename.md|old_content|new_content'", "input": input_str}

        filename = parts[0].strip()
        if not filename.endswith('.md'):
            filename += '.md'

        # Check if this is line-based editing (parts[1] and parts[2] are numbers)
        try:
            if len(parts) == 4:
                start_line = int(parts[1].strip())
                end_line = int(parts[2].strip())
                new_content = parts[3]
                
                # Line-based editing
                return _edit_by_lines(filename, start_line, end_line, new_content)
        except (ValueError, IndexError):
            # Not line-based, fall through to content-based
            pass

        # Content-based editing (legacy approach)
        if len(parts) != 3:
            return {"success": False, "error": "For content-based editing, use format 'filename.md|old_content|new_content'", "input": input_str}
        
        old_content = parts[1]
        new_content = parts[2]
        
        return _edit_by_content(filename, old_content, new_content)
        
    except FileNotFoundError:
        return {"success": False, "error": f"File {filename} not found", "input": input_str}
    except Exception as e:
        return {"success": False, "error": str(e), "input": input_str}


def _edit_by_lines(filename: str, start_line: int, end_line: int, new_content: str):
    """
    Edit specific lines in a file. More efficient than full file replacement.
    Lines are 1-indexed (start_line=1 means first line).
    """
    try:
        # Read all lines
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        
        # Validate line numbers
        if start_line < 1 or start_line > total_lines:
            return {
                "success": False,
                "error": f"start_line {start_line} is out of range (file has {total_lines} lines)"
            }
        
        if end_line < start_line or end_line > total_lines:
            return {
                "success": False,
                "error": f"end_line {end_line} is invalid (must be >= {start_line} and <= {total_lines})"
            }
        
        # Convert to 0-indexed
        start_idx = start_line - 1
        end_idx = end_line  # end_line is inclusive, so we don't subtract 1 for slicing
        
        # Ensure new_content ends with newline if it doesn't already
        if new_content and not new_content.endswith('\n'):
            new_content += '\n'
        
        # Replace the specified lines
        updated_lines = lines[:start_idx] + [new_content] + lines[end_idx:]
        
        # Write back only the modified content
        with open(filename, 'w', encoding='utf-8') as f:
            f.writelines(updated_lines)
        
        return {
            "success": True,
            "message": f"File {filename} updated: lines {start_line}-{end_line} replaced",
            "filename": filename,
            "lines_replaced": end_line - start_line + 1
        }
    except Exception as e:
        return {"success": False, "error": str(e), "filename": filename}


def _edit_by_content(filename: str, old_content: str, new_content: str):
    """
    Legacy content-based editing. Reads entire file, replaces content, writes back.
    Less efficient but useful when line numbers are unknown.
    """
    try:
        # Read current content
        with open(filename, 'r', encoding='utf-8') as f:
            current_content = f.read()

        # Normalize content for better matching
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
                "suggestion": "Consider using line-based editing 'filename.md|start_line|end_line|new_content' or write_md_file to overwrite the entire file."
            }

        # Write back
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(updated_content)

        return {
            "success": True,
            "message": f"File {filename} updated successfully (content-based replacement)",
            "filename": filename,
            "note": "Consider using line-based editing for better efficiency"
        }
    except Exception as e:
        return {"success": False, "error": str(e), "filename": filename}

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

    ## File Editing Instructions (CRITICAL - EFFICIENCY FIRST):
    
    ### PREFERRED: Line-Based Editing (Use This 95% of the Time)
    - **ALWAYS use edit_md_file with line-based editing** for updating existing documentation
    - Format: 'filename.md|start_line|end_line|new_content'
    - This is MUCH more efficient than rewriting entire files
    - Only modifies the specific section that changed
    
    ### Workflow for Line-Based Editing:
    1. Use check_git_status() to identify changed files
    2. Use read_file() to examine changed files and understand feature modifications
    3. Use read_md_file() to read the CURRENT FEATUREREADME.md - it returns content WITH LINE NUMBERS (format: "LINE | CONTENT")
    4. **IDENTIFY the exact line range** that needs updating by reading the numbered output (e.g., lines 90-110 for "Feature 4" section)
    5. Use edit_md_file('FEATUREREADME.md|start_line|end_line|new_content') to update ONLY that section
    6. If multiple sections need updates, call edit_md_file multiple times with different line ranges
    
    ### PRO TIP: read_md_file automatically shows line numbers!
    When you call read_md_file, the output includes line numbers like:
      90 | ### 4. Markdown File Management
      91 | This project provides advanced utilities...
      92 | - **Reading, writing, and editing...**
    This makes it EASY to identify exactly which lines to edit!
    
    ### When to Use Each Tool:
    - **edit_md_file (line-based)**: 95% of updates - updating existing sections, adding features, modifying API docs
    - **write_md_file**: Only for creating NEW files or when the entire structure needs complete rewrite
    - **edit_md_file (content-based)**: Legacy fallback, avoid if possible
    
    ### Important Rules:
    - Use check_git_status() first to identify changed files
    - Use read_file() to examine changed files and understand feature modifications  
    - ALWAYS read the markdown file first to see line numbers before editing
    - Calculate the correct start_line and end_line for the section you want to update
    - Always target FEATUREREADME.md as the main documentation file, not README.md
    - Do NOT rewrite entire files unless absolutely necessary
    - Generate detailed documentation content for the specific sections being updated

    ## Example Workflow for Feature Documentation (LINE-BASED EDITING):
    1. Plan: {{ "step": "plan", "content": "Need to analyze changed files to understand what features were modified" }}
    2. Action: {{ "step": "action", "function": "check_git_status", "input": "" }}
    3. Observe: {{ "step": "observe", "content": "Found changes in generate_feature_docs.py - analyzing modifications..." }}
    4. Action: {{ "step": "action", "function": "read_file", "input": "generate_feature_docs.py" }}
    5. Observe: {{ "step": "observe", "content": "The edit_md_file function now supports line-based editing. Feature 4 section needs updating..." }}
    6. Action: {{ "step": "action", "function": "read_md_file", "input": "FEATUREREADME.md" }}
    7. Observe: {{ "step": "observe", "content": "Current FEATUREREADME.md has Feature 4 section at lines 90-110. Will update this section only..." }}
    8. Write: {{ "step": "write", "content": "Updating lines 90-110 to document the new line-based editing capability..." }}
    9. Action: {{ "step": "action", "function": "edit_md_file", "input": "FEATUREREADME.md|90|110|### 4. Markdown File Management & Developer Utilities\\n\\nUpdated content with line-based editing docs..." }}
    10. Output: {{ "step": "output", "content": "FEATUREREADME.md updated efficiently using line-based editing (only modified lines 90-110)" }}

    ## Example: Multiple Section Updates
    If you need to update multiple sections:
    1. Read the file to identify all line ranges
    2. Call edit_md_file once for each section:
       - edit_md_file('FEATUREREADME.md|90|110|new_feature_4_content')
       - edit_md_file('FEATUREREADME.md|200|225|new_api_reference_content')
       - edit_md_file('FEATUREREADME.md|250|270|new_examples_content')

    IMPORTANT: Only modify FEATUREREADME.md, never README.md. All documentation updates should target FEATUREREADME.md.

    CRITICAL WORKFLOW REMINDER:
    - You MUST use edit_md_file (line-based) for documentation updates before reaching the "output" step
    - Do NOT use write_md_file unless creating a completely new file
    - Read the markdown file FIRST to identify line numbers
    - Only modify the specific sections that changed
    - Do NOT provide an "output" response until you have successfully edited the documentation
    - The workflow should end with actual file changes using efficient line-based editing

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