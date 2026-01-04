
import json
import os
import asyncio
import time
from typing import Dict, List, Any, Optional, TypedDict
from agents import Agent, function_tool, Runner
from services.notion import NotionService
from env import LLM_API_KEY

# Set OpenAI API key for agents SDK
os.environ["OPENAI_API_KEY"] = LLM_API_KEY

# Initialize services
notion_service = NotionService()


# TypedDict for content blocks structure
class ContentBlock(TypedDict, total=False):
    """Structure for Notion content blocks"""
    type: str
    text: str
    extra: str

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
# AGENT CREATION
# ============================================================================

# Collect all tools
ALL_TOOLS = [
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
]

async def judge_notion_docs(
    page_id: str,
    max_iterations: int = 50
):
    """
    Review and fix quality issues in Notion documentation using OpenAI Agents SDK.
    
    Args:
        page_id: Existing Notion page ID to review and update
        max_iterations: Maximum number of iterations (default 50)
        
    Returns:
        Dictionary with review results
    """
    try:
        print(f"🔧 Starting judge_notion_docs function...")
        print(f"📊 Parameters:")
        print(f"   - page_id: {page_id}")
        print(f"   - max_iterations: {max_iterations}")
        
        # Check environment variables
        print(f"🔐 Environment check:")
        print(f"   - LLM_API_KEY: {'SET' if LLM_API_KEY else 'NOT SET'}")
        print(f"   - OPENAI_API_KEY env: {'SET' if os.environ.get('OPENAI_API_KEY') else 'NOT SET'}")
        
        from prompts.judge_prompt import get_judge_prompt
        print(f"✅ Successfully imported prompt function")
        
        # Build context
        context_info = f"TARGET PAGE ID: {page_id}\n"
        context_info += "Review this Notion page for quality issues and fix them automatically.\n"
        
        print(f"📝 Context info prepared: {len(context_info)} characters")
        
        # Create agent
        print(f"🤖 Creating agent...")
        system_prompt = get_judge_prompt(context_info)
        print(f"📋 System prompt created: {len(system_prompt)} characters")
        
        try:
            agent = Agent(
                name="Documentation Quality Judge",
                instructions=system_prompt,
                tools=ALL_TOOLS,
                model="gpt-5-nano"
            )
            print(f"✅ Agent created successfully")
        except Exception as agent_error:
            print(f"❌ Agent creation failed: {agent_error}")
            raise
        
        # Build task
        task = f"Review and improve the quality of the Notion documentation page {page_id}. "
        task += "Read the page content, identify all quality issues (grammar, formatting, spacing, content quality), "
        task += "and fix them automatically using the available tools."
        
        print(f"📋 Task: {task}")
        
        print(f"\n{'='*60}")
        print(f"🚀 RUNNING JUDGE AGENT")
        print(f"{'='*60}\n")
        
        # Run agent asynchronously with retry logic for rate limits
        max_turns_value = 50
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
                break  # Success, exit retry loop
                
            except Exception as run_error:
                error_str = str(run_error)
                print(f"❌ Agent execution failed: {error_str}")

        print(f"\n{'='*60}")
        print(f"✅ JUDGE AGENT COMPLETED")
        print(f"{'='*60}\n")
        
        judge_result = {
            "content": str(agent_result.final_output) if hasattr(agent_result, 'final_output') else str(agent_result),
            "iterations": "N/A (SDK managed)"
        }
        
        result = {
            "judge_result": judge_result,
            "reviewed_page_id": page_id
        }
        
    except Exception as e:
        print(f"❌ Error in judge_notion_docs: {e}")
        import traceback
        print(f"🔍 Traceback: {traceback.format_exc()}")
        return {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "success": False,
            "reviewed_page_id": page_id
        }
    
    return result