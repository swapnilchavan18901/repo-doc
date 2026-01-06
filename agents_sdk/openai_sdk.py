
import json
import os
import asyncio
import time
from typing import Dict, List, Any, Optional, TypedDict
from agents import Agent, function_tool, Runner
from services.github_actions import GitHubService
from services.notion import NotionService
from agents_sdk.judge_sdk import judge_notion_docs
from env import LLM_API_KEY

# Set OpenAI API key for agents SDK
os.environ["OPENAI_API_KEY"] = LLM_API_KEY

# Initialize services
github_service = GitHubService()
notion_service = NotionService()


# TypedDict for content blocks structure
class ContentBlock(TypedDict, total=False):
    """Structure for Notion content blocks"""
    type: str
    text: str
    extra: str


# ============================================================================
# GITHUB TOOLS
# ============================================================================

@function_tool
def get_github_diff(repo_full_name: str, before_sha: str, after_sha: str) -> Dict[str, Any]:
    """
    Get the diff between two commits showing all file changes with patches.
    
    Args:
        repo_full_name: Repository full name in format 'owner/repo'
        before_sha: The commit SHA before changes
        after_sha: The commit SHA after changes
        
    Returns:
        Dictionary with success status, files changed, and diff details
    """
    input_str = f"{repo_full_name}|{before_sha}|{after_sha}"
    return github_service.get_diff(input_str)


@function_tool
def get_github_file_tree(repo_full_name: str, sha: str, path: str = "") -> Dict[str, Any]:
    """
    Get the file tree/directory structure of the repository (one level only).
    
    Args:
        repo_full_name: Repository full name in format 'owner/repo'
        sha: Commit SHA or branch name (e.g., 'main')
        path: Directory path to list (empty string for root)
        
    Returns:
        Dictionary with success status and directory contents
    """
    input_str = f"{repo_full_name}|{sha}|{path}"
    return github_service.get_file_tree(input_str)


@function_tool
def read_github_file(repo_full_name: str, filepath: str, sha: str = "main") -> Dict[str, Any]:
    """
    Read the complete content of a specific file from GitHub repository.
    
    Args:
        repo_full_name: Repository full name in format 'owner/repo'
        filepath: Path to the file in the repository
        sha: Commit SHA or branch name (defaults to 'main')
        
    Returns:
        Dictionary with success status and file content
    """
    input_str = f"{repo_full_name}|{filepath}|{sha}"
    return github_service.read_file(input_str)


@function_tool
def search_github_code(repo_full_name: str, query: str, max_results: int = 10) -> Dict[str, Any]:
    """
    Search for code in the repository using keywords or patterns.
    
    Args:
        repo_full_name: Repository full name in format 'owner/repo'
        query: Search query (keywords, function names, class names, etc.)
        max_results: Maximum number of results to return (default 10)
        
    Returns:
        Dictionary with success status and search results
    """
    input_str = f"{repo_full_name}|{query}|{max_results}"
    return github_service.search_code(input_str)


@function_tool
def list_all_github_files(repo_full_name: str, sha: str , path: str = "") -> Dict[str, Any]:
    """
    Recursively list ALL files in the repository (flat list, all directories).
    Best for understanding complete project structure.
    
    Args:
        repo_full_name: Repository full name in format 'owner/repo'
        sha: Commit SHA or branch name (defaults to 'main')
        path: Starting path (empty string for entire repo)
        
    Returns:
        Dictionary with success status and complete file listing
    """
    input_str = f"{repo_full_name}|{sha}|{path}"
    return github_service.list_all_files_recursive(input_str)


# ============================================================================
# NOTION TOOLS
# ============================================================================

@function_tool
def get_notion_databases() -> Dict[str, Any]:
    """
    List all Notion databases you have access to.
    
    Returns:
        Dictionary with success status and list of databases with IDs and titles
    """
    return notion_service.get_all_databases("")


@function_tool
def search_page_by_title(page_title: str) -> Dict[str, Any]:
    """
    Search for a Notion page by exact title match.
    
    Args:
        page_title: The exact title of the page to search for
        
    Returns:
        Dictionary with success status, found flag, and page details if found
    """
    return notion_service.search_page_by_title(page_title)


@function_tool
def get_notion_page_content(page_id: str) -> Dict[str, Any]:
    """
    Read all content blocks from a Notion page, organized by sections.
    
    Args:
        page_id: The Notion page ID
        
    Returns:
        Dictionary with success status and page content organized by sections
    """
    return notion_service.get_page_content(page_id)


@function_tool
def query_database_pages(database_id: str, page_size: int = 10) -> Dict[str, Any]:
    """
    Query pages from a database, sorted by creation time (most recent first).
    
    Args:
        database_id: The Notion database ID
        page_size: Number of pages to return (default 10)
        
    Returns:
        Dictionary with success status and list of pages
    """
    input_str = f"{database_id}|{page_size}"
    return notion_service.query_database_pages(input_str)


@function_tool
def create_notion_doc_page(database_id: str, page_title: str) -> Dict[str, Any]:
    """
    Create a new blank page in a Notion database.
    
    Args:
        database_id: The Notion database ID where the page will be created
        page_title: The title for the new page
        
    Returns:
        Dictionary with success status, page_id, and URL
    """
    input_str = f"{database_id}|{page_title}"
    return notion_service.create_doc_page(input_str)


@function_tool
def add_block_to_page(
    page_id: str,
    block_type: str,
    text: str = "",
    extra_param: str = ""
) -> Dict[str, Any]:
    """
    Create and append a single block to the end of a page.
    Use for headings, paragraphs, code blocks, callouts, dividers.
    For multiple bullets/numbered items, use batch functions instead.
    
    Args:
        page_id: The Notion page ID
        block_type: Block type (h1, h2, h3, paragraph, bullet, numbered, quote, code, callout, todo, divider, toc)
        text: The text content for the block
        extra_param: Extra parameter (for code=language, for callout=emoji, for todo='true'/'false')
        
    Returns:
        Dictionary with success status and confirmation message
    """
    if extra_param:
        input_str = f"{page_id}|{block_type}|{text}|{extra_param}"
    else:
        input_str = f"{page_id}|{block_type}|{text}"
    return notion_service.add_block_to_page(input_str)


@function_tool
def add_bullets_batch(page_id: str, bullets: List[str]) -> Dict[str, Any]:
    """
    Add multiple bullet points in ONE API call (much faster and cheaper than individual bullets).
    ALWAYS use this for 2+ bullet points.
    
    Args:
        page_id: The Notion page ID
        bullets: List of bullet point texts
        
    Returns:
        Dictionary with success status and number of blocks added
    """
    bullets_str = "##".join(bullets)
    input_str = f"{page_id}|{bullets_str}"
    return notion_service.add_bullets_batch(input_str)


@function_tool
def add_numbered_batch(page_id: str, items: List[str]) -> Dict[str, Any]:
    """
    Add multiple numbered list items in ONE API call (much faster and cheaper).
    ALWAYS use this for 2+ numbered items.
    
    Args:
        page_id: The Notion page ID
        items: List of numbered item texts
        
    Returns:
        Dictionary with success status and number of blocks added
    """
    items_str = "##".join(items)
    input_str = f"{page_id}|{items_str}"
    return notion_service.add_numbered_batch(input_str)


@function_tool
def add_paragraphs_batch(page_id: str, paragraphs: List[str]) -> Dict[str, Any]:
    """
    Add multiple paragraphs in ONE API call (faster for multi-paragraph content).
    
    Args:
        page_id: The Notion page ID
        paragraphs: List of paragraph texts
        
    Returns:
        Dictionary with success status and number of blocks added
    """
    paras_str = "##".join(paragraphs)
    input_str = f"{page_id}|{paras_str}"
    return notion_service.add_paragraphs_batch(input_str)


@function_tool
def update_notion_section(
    page_id: str,
    heading_text: str,
    content_blocks: List[ContentBlock]
) -> Dict[str, Any]:
    """
    Replace all content under a specific heading with new blocks (mixed types supported).
    Use with caution - this deletes old content.
    
    Args:
        page_id: The Notion page ID
        heading_text: The exact heading text to find
        content_blocks: List of dicts with 'type' and 'text' keys. Types: h1, h2, h3, paragraph, bullet, numbered, code, callout, quote
                       Optional 'extra' key for code language or callout emoji.
                       Example: [
                           {"type": "paragraph", "text": "Updated intro"},
                           {"type": "bullet", "text": "New point 1"},
                           {"type": "bullet", "text": "New point 2"}
                       ]
        
    Returns:
        Dictionary with success status and number of replaced blocks
    """
    
    
    # Create blocks from the list of block definitions
    notion_blocks = []
    for block in content_blocks:
        block_type = block.get("type", "paragraph")
        text = block.get("text", "")
        extra = block.get("extra", "")
        
        if block_type == "h1":
            notion_blocks.append(notion_service.h1(text))
        elif block_type == "h2":
            notion_blocks.append(notion_service.h2(text))
        elif block_type == "h3":
            notion_blocks.append(notion_service.h3(text))
        elif block_type == "paragraph":
            notion_blocks.append(notion_service.paragraph(text))
        elif block_type == "bullet":
            notion_blocks.append(notion_service.bullet(text))
        elif block_type == "numbered":
            notion_blocks.append(notion_service.numbered(text))
        elif block_type == "code":
            language = extra if extra else "python"
            notion_blocks.append(notion_service.code(text, language))
        elif block_type == "callout":
            emoji = extra if extra else "💡"
            notion_blocks.append(notion_service.callout(text, emoji))
        elif block_type == "quote":
            notion_blocks.append(notion_service.quote(text))
        elif block_type == "divider":
            notion_blocks.append(notion_service.divider())
        else:
            notion_blocks.append(notion_service.paragraph(text))
    
    blocks_json = json.dumps(notion_blocks)
    input_str = f"{page_id}|{heading_text}|{blocks_json}"
    return notion_service.replace_section(input_str)


@function_tool
def insert_blocks_after_text(
    page_id: str,
    after_text: str,
    blocks: List[ContentBlock]
) -> Dict[str, Any]:
    """
    Insert blocks after a specific text block (searches by exact text match).
    Supports mixed block types (h1, h2, h3, paragraph, bullet, code, etc.).
    
    Args:
        page_id: The Notion page ID
        after_text: The exact text to find
        blocks: List of dicts with 'type' and 'text' keys. Types: h1, h2, h3, paragraph, bullet, numbered, code, callout, quote
               Optional 'extra' key for code language or callout emoji.
               Example: [
                   {"type": "h3", "text": "New Subsection"},
                   {"type": "paragraph", "text": "Some explanation"},
                   {"type": "code", "text": "code example", "extra": "python"}
               ]
        
    Returns:
        Dictionary with success status and number of inserted blocks
    """
    
    # Create blocks from the list of block definitions
    notion_blocks = []
    for block in blocks:
        block_type = block.get("type", "paragraph")
        text = block.get("text", "")
        extra = block.get("extra", "")
        
        if block_type == "h1":
            notion_blocks.append(notion_service.h1(text))
        elif block_type == "h2":
            notion_blocks.append(notion_service.h2(text))
        elif block_type == "h3":
            notion_blocks.append(notion_service.h3(text))
        elif block_type == "paragraph":
            notion_blocks.append(notion_service.paragraph(text))
        elif block_type == "bullet":
            notion_blocks.append(notion_service.bullet(text))
        elif block_type == "numbered":
            notion_blocks.append(notion_service.numbered(text))
        elif block_type == "code":
            language = extra if extra else "python"
            notion_blocks.append(notion_service.code(text, language))
        elif block_type == "callout":
            emoji = extra if extra else "💡"
            notion_blocks.append(notion_service.callout(text, emoji))
        elif block_type == "quote":
            notion_blocks.append(notion_service.quote(text))
        elif block_type == "divider":
            notion_blocks.append(notion_service.divider())
        else:
            notion_blocks.append(notion_service.paragraph(text))
    
    blocks_json = json.dumps(notion_blocks)
    input_str = f"{page_id}|{after_text}|{blocks_json}"
    return notion_service.insert_between_by_text(input_str)


@function_tool
def append_paragraphs(page_id: str, paragraphs: List[str]) -> Dict[str, Any]:
    """
    Append multiple paragraphs to the end of a page.
    Note: For bullets or numbered lists, use add_bullets_batch or add_numbered_batch instead.
    
    Args:
        page_id: The Notion page ID
        paragraphs: List of paragraph texts to append
        
    Returns:
        Dictionary with success status and number of blocks added
    """
    # Just use the existing add_paragraphs_batch function
    return add_paragraphs_batch(page_id, paragraphs)


@function_tool
def add_mixed_blocks(page_id: str, blocks: List[ContentBlock]) -> Dict[str, Any]:
    """
    Add multiple blocks of different types at once (h1, h2, h3, paragraph, bullet, etc.).
    Use this when you need to add different block types in one call.
    
    Args:
        page_id: The Notion page ID
        blocks: List of dicts with 'type' and 'text' keys. Types: h1, h2, h3, paragraph, bullet, numbered, code, callout, quote
                Optional 'extra' key for code language or callout emoji.
                Example: [
                    {"type": "h2", "text": "Overview"},
                    {"type": "paragraph", "text": "This is intro text."},
                    {"type": "bullet", "text": "Feature 1"},
                    {"type": "code", "text": "print('hello')", "extra": "python"}
                ]
        
    Returns:
        Dictionary with success status and number of blocks added
    """
    
    
    # Map block types to notion_service methods
    notion_blocks = []
    for block in blocks:
        block_type = block.get("type", "paragraph")
        text = block.get("text", "")
        extra = block.get("extra", "")
        
        if block_type == "h1":
            notion_blocks.append(notion_service.h1(text))
        elif block_type == "h2":
            notion_blocks.append(notion_service.h2(text))
        elif block_type == "h3":
            notion_blocks.append(notion_service.h3(text))
        elif block_type == "paragraph":
            notion_blocks.append(notion_service.paragraph(text))
        elif block_type == "bullet":
            notion_blocks.append(notion_service.bullet(text))
        elif block_type == "numbered":
            notion_blocks.append(notion_service.numbered(text))
        elif block_type == "code":
            language = extra if extra else "python"
            notion_blocks.append(notion_service.code(text, language))
        elif block_type == "callout":
            emoji = extra if extra else "💡"
            notion_blocks.append(notion_service.callout(text, emoji))
        elif block_type == "quote":
            notion_blocks.append(notion_service.quote(text))
        elif block_type == "divider":
            notion_blocks.append(notion_service.divider())
        elif block_type == "toc":
            notion_blocks.append(notion_service.table_of_contents())
        else:
            # Default to paragraph
            notion_blocks.append(notion_service.paragraph(text))
    
    blocks_json = json.dumps(notion_blocks)
    input_str = f"{page_id}|{blocks_json}"
    return notion_service.append_blocks(input_str)


# ============================================================================
# JUDGE AGENT AS TOOL (WITH DYNAMIC CONTEXT)
# ============================================================================

from prompts.judge_prompt import get_judge_prompt

@function_tool
def review_documentation_quality(
    page_id: str,
    context: str = "",
    repo_full_name: str = "",
    database_id: str = ""
) -> Dict[str, Any]:
    """
    Analyze Notion documentation quality and provide detailed feedback on issues.
    
    This tool runs a specialized judge agent that thoroughly analyzes the documentation
    and returns a comprehensive quality report with specific, actionable recommendations.
    
    Use this AFTER creating or updating documentation to get quality analysis.
    Then fix any issues identified by the judge using appropriate Notion tools.
    
    Args:
        page_id: The Notion page ID to analyze (REQUIRED)
        context: Additional context about the documentation (optional)
        repo_full_name: GitHub repository name if applicable (optional)
        database_id: Notion database ID if applicable (optional)
        
    Returns:
        Detailed analysis report with:
        - Overall quality score (0-100)
        - Section-by-section analysis
        - Critical/major/minor issues found
        - Specific recommendations for fixes
        - Priority actions to take
    
    Example:
        review_documentation_quality(
            page_id="abc123",
            context="Technical documentation for API service",
            repo_full_name="myorg/myrepo"
        )
    """
    try:
        print(f"\n{'='*60}")
        print(f"🔍 STARTING QUALITY ANALYSIS")
        print(f"{'='*60}")
        print(f"📄 Page ID: {page_id}")
        if repo_full_name:
            print(f"📦 Repository: {repo_full_name}")
        if database_id:
            print(f"🗄️  Database ID: {database_id}")
        if context:
            print(f"📝 Context: {context}")
        print(f"{'='*60}\n")
        
        # Build dynamic context for judge
        judge_context = f"TARGET PAGE ID: {page_id}\n\n"
        
        if repo_full_name:
            judge_context += f"REPOSITORY: {repo_full_name}\n"
        if database_id:
            judge_context += f"DATABASE ID: {database_id}\n"
        if context:
            judge_context += f"ADDITIONAL CONTEXT: {context}\n"
        
        judge_context += "\nYour task: Analyze this Notion documentation page and provide comprehensive quality feedback.\n"
        
        # Create judge agent with dynamic context
        judge_agent = Agent(
            name="Documentation Quality Judge",
            instructions=get_judge_prompt(judge_context),
            tools=[
                get_notion_page_content,
            ],
            model="gpt-5-nano"
        )
        
        # Build analysis task
        task = f"Analyze the quality of documentation page {page_id}. "
        task += "Provide a thorough analysis covering completeness, clarity, accuracy, formatting, and professionalism. "
        task += "Return a detailed report with specific, actionable recommendations."
        
        print(f"🤖 Creating judge agent with context...")
        print(f"📋 Analysis task: {task}\n")
        
        # Run judge agent
        runner = Runner()
        result = runner.run_sync(agent=judge_agent, task=task, max_turns=20)
        
        print(f"\n{'='*60}")
        print(f"✅ QUALITY ANALYSIS COMPLETED")
        print(f"{'='*60}\n")
        
        # Extract the analysis from result
        analysis_output = str(result.final_output) if hasattr(result, 'final_output') else str(result)
        
        return {
            "success": True,
            "page_id": page_id,
            "analysis": analysis_output,
            "message": "Quality analysis completed successfully. Review the analysis and apply recommended fixes."
        }
        
    except Exception as e:
        print(f"\n❌ Quality analysis failed: {e}")
        import traceback
        print(f"🔍 Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "page_id": page_id,
            "error": str(e),
            "message": f"Quality analysis failed: {str(e)}"
        }


# ============================================================================
# AGENT CREATION
# ============================================================================

# Collect all tools
ALL_TOOLS = [
    # GitHub tools
    get_github_diff,
    get_github_file_tree,
    read_github_file,
    search_github_code,
    list_all_github_files,
    # Notion tools
    get_notion_databases,
    search_page_by_title,
    get_notion_page_content,
    query_database_pages,
    create_notion_doc_page,
    add_block_to_page,
    add_bullets_batch,
    add_numbered_batch,
    add_paragraphs_batch,
    add_mixed_blocks,
    update_notion_section,
    insert_blocks_after_text,
    append_paragraphs,
    # Judge agent as tool (with dynamic context support)
    review_documentation_quality,
]

async def generate_notion_docs(
    repo_full_name: str = None,
    before_sha: str = None,
    after_sha: str = None,
    database_id: str = None,
    page_id: str = None,
    max_iterations: int = 100
):
    """
    Generate Notion documentation using OpenAI Agents SDK.
    Drop-in replacement for the LiteLLM version.
    
    Args:
        repo_full_name: GitHub repository 'owner/repo'
        before_sha: Commit SHA before changes
        after_sha: Commit SHA after changes  
        database_id: Notion database ID to create page in
        page_id: Existing Notion page ID to update
        max_iterations: Not used (SDK manages iterations)
        
    Returns:
        Dictionary with generation results
    """
    #here
    try:
        print(f"🔧 Starting generate_notion_docs function...")
        print(f"📊 Parameters:")
        print(f"   - repo_full_name: {repo_full_name}")
        print(f"   - before_sha: {before_sha}")
        print(f"   - after_sha: {after_sha}")
        print(f"   - database_id: {database_id}")
        print(f"   - page_id: {page_id}")
        
        # Check environment variables
        print(f"🔐 Environment check:")
        print(f"   - LLM_API_KEY: {'SET' if LLM_API_KEY else 'NOT SET'}")
        print(f"   - OPENAI_API_KEY env: {'SET' if os.environ.get('OPENAI_API_KEY') else 'NOT SET'}")
        
        from prompts.openai_agent_prompt import get_openai_agent_prompt
        print(f"✅ Successfully imported prompt function")
        # Build context
        context_info = ""
        if repo_full_name and before_sha and after_sha:
            context_info += f"GITHUB REPOSITORY: {repo_full_name}\n"
            context_info += f"COMMIT RANGE: {before_sha[:7]}...{after_sha[:7]}\n\n"
        
        if database_id:
            context_info += f"TARGET DATABASE ID: {database_id} (create new page)\n"
        if page_id:
            context_info += f"TARGET PAGE ID: {page_id} (update existing page)\n"
        if not database_id and not page_id:
            context_info += "NO TARGET SPECIFIED: Discover databases and create/identify page.\n"
        
        print(f"📝 Context info prepared: {len(context_info)} characters")
        
        # Create agent
        print(f"🤖 Creating agent...")
        system_prompt = get_openai_agent_prompt(context_info)
        print(f"📋 System prompt created: {len(system_prompt)} characters")
        
        
        try:
            agent = Agent(
                name="Documentation Generator",
                instructions=system_prompt,
                tools=ALL_TOOLS,
                model="gpt-5-nano"
            )
            print(f"✅ Agent created successfully")
        except Exception as agent_error:
            print(f"❌ Agent creation failed: {agent_error}")
            raise
        
        # Build task
        task = "Generate comprehensive technical documentation. "

        if repo_full_name:
            task += f"Analyze repository {repo_full_name}. "
        if database_id:
            task += f"Create page in database {database_id}. "
        elif page_id:
            task += f"Update page {page_id}. "
        
        task += "\n\nMANDATORY QUALITY CYCLE: After creating documentation, you MUST: (1) Call review_documentation_quality with page_id and context, (2) Fix ALL critical and major issues using appropriate Notion tools, (3) Re-review to confirm fixes, (4) Iterate until quality score ≥ 80 or status is 'excellent'/'good'. Do NOT skip this cycle."
        
        print(f"📋 Task: {task}")
        
        print(f"\n{'='*60}")
        print(f"🚀 RUNNING OPENAI AGENT")
        print(f"{'='*60}\n")
        
        # Run agent asynchronously with retry logic for rate limits
        # Since Runner.run_sync() can't be called in an event loop,
        # we run it in a separate thread using asyncio.to_thread()
        max_turns_value = 100
        print(f"⚙️  Max turns set to: {max_turns_value}")
        
        # Retry configuration for rate limits
        max_retries = 5
        base_delay = 5  # Start with 5 seconds
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                if retry_count > 0:
                    print(f"🔄 Retry attempt {retry_count}/{max_retries} after rate limit...")
                
                print(f"🔄 Running agent in thread pool to avoid event loop conflict...")
                agent_result = await asyncio.to_thread(
                    Runner.run_sync, 
                    agent, 
                    task,
                    max_turns=max_turns_value
                )
                print(f"✅ Agent execution completed")
                
                print(f"📊 Result type: {type(agent_result)}")
                print(f"📊 Result attributes: {dir(agent_result)}")
                break  # Success, exit retry loop
                
            except Exception as run_error:
                error_str = str(run_error)
                print(f"❌ Agent execution failed: {error_str}")
        
        print(f"\n{'='*60}")
        
        print(f"✅ AGENT COMPLETED")
        print(f"{'='*60}\n")
        
        result = {
            "content": str(agent_result.final_output) if hasattr(agent_result, 'final_output') else str(agent_result),
            "iterations": "N/A (SDK managed)",
            "success": True
        }
        
        return result
        
    except Exception as e:
        print(f"❌ Error in generate_notion_docs: {e}")
        import traceback
        print(f"🔍 Traceback: {traceback.format_exc()}")
        return {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "success": False
        }