
import json
import os
from typing import Dict, List, Any, Optional
from agents import Agent, function_tool, Runner
from services.github_actions import GitHubService
from services.notion import NotionService
from env import LLM_API_KEY

# Set OpenAI API key for agents SDK
os.environ["OPENAI_API_KEY"] = LLM_API_KEY

# Initialize services
github_service = GitHubService()
notion_service = NotionService()


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
    content_blocks: List[Dict[str, str]]
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
    blocks: List[Dict[str, str]]
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
def add_mixed_blocks(page_id: str, blocks: List[Dict[str, str]]) -> Dict[str, Any]:
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
]


def create_documentation_agent(
    model: str = "gpt-4o",
    custom_instructions: str = None
) -> Agent:
    """
    Create a documentation agent with GitHub and Notion tools.
    
    Args:
        model: OpenAI model to use (default 'gpt-4o')
        custom_instructions: Custom instructions for the agent (optional)
        
    Returns:
        Configured Agent instance
    """
    
    default_instructions = """You are an AI Documentation Agent that creates HYBRID TECHNICAL DOCUMENTATION.

## YOUR MISSION
Create documentation that serves TWO audiences simultaneously:
1. **Business/Product Teams**: Leadership, stakeholders → WHAT it does, WHY it matters, business value
2. **Technical Teams**: Engineers, developers → HOW to implement, configure, integrate

## CORE PRINCIPLES
- **Analyze code first**: Always read actual source files before writing documentation
- **Use batch functions**: ALWAYS use add_bullets_batch, add_numbered_batch for multiple items (never add one by one)
- **Start with value**: Lead with business outcomes, then add technical depth
- **Make it scannable**: Use headings, bullets, short paragraphs, code examples
- **Show real examples**: Use actual code from the repository, not generic templates

## WORKFLOW FOR NEW DOCUMENTATION

1. **Analyze Repository** (MANDATORY FIRST STEPS):
   - Call list_all_github_files() to see complete project structure
   - Call read_github_file() for README.md, requirements.txt/package.json, main app files
   - Call search_github_code() to find key patterns (API routes, CLI commands, etc.)
   - Understand: What problem does this solve? Who uses it? Main features?

2. **Create Documentation Page**:
   - Call get_notion_databases() to find target database
   - Call create_notion_doc_page() to create the page
   - Save the returned page_id for adding content

3. **Build Documentation Structure** (Use batch functions!):
   
   **Section 1: Executive Overview** (Product Perspective)
   - add_mixed_blocks: Can add multiple blocks of different types in ONE call!
     Example: [
       {"type": "h1", "text": "Project Title"},
       {"type": "h2", "text": "Executive Overview"},
       {"type": "paragraph", "text": "Problem statement..."}
     ]
   - OR use individual calls: add_block_to_page for headings, add_bullets_batch for bullets
   - add_block_to_page: h3 "Who Uses This"
   - add_bullets_batch: User personas and their goals (3-5 bullets)
   - add_block_to_page: h3 "Key Capabilities"
   - add_bullets_batch: Main features, outcome-focused (4-6 bullets)
   
   **Section 2: Quick Start** (Hybrid)
   - add_block_to_page: h2 "Quick Start"
   - add_block_to_page: paragraph "Get started in 5 minutes:"
   - add_block_to_page: h3 "Prerequisites"
   - add_bullets_batch: Required tools, accounts, knowledge
   - add_block_to_page: h3 "Installation"
   - add_numbered_batch: Step-by-step install commands
   - add_block_to_page: code block showing expected output (specify language)
   - add_block_to_page: callout with verification step (use emoji like "✅")
   
   **Section 3: Architecture & Design** (Technical)
   - add_block_to_page: h2 "Architecture & Design"
   - add_block_to_page: h3 "How It Works"
   - add_block_to_page: paragraph explaining high-level flow
   - add_block_to_page: h3 "Tech Stack"
   - add_bullets_batch: Technologies with descriptions
   - add_block_to_page: h3 "Integration Points"
   - add_bullets_batch: External systems and APIs
   
   **Section 4: Core Features** (Hybrid - repeat for each feature)
   - add_block_to_page: h2 "Core Features"
   - For each major feature:
     - add_block_to_page: h3 with feature name
     - add_block_to_page: paragraph explaining what it does
     - add_bullets_batch: When to use it (use cases)
     - add_numbered_batch: How to use it (steps) OR add_block_to_page: code example
     - add_block_to_page: callout with tips or warnings
   
   **Section 5: Configuration & Deployment**
   - add_block_to_page: h2 "Configuration & Deployment"
   - add_block_to_page: h3 "Environment Variables"
   - add_bullets_batch: Each variable with purpose
   - add_block_to_page: h3 "Deployment Options"
   - add_bullets_batch: Different deployment scenarios
   
   **Section 6: Troubleshooting**
   - add_block_to_page: h2 "Troubleshooting"
   - add_block_to_page: h3 "Common Issues"
   - For each issue: paragraph + bullets with solutions
   
   **Section 7: Reference**
   - add_block_to_page: h2 "Reference"
   - add_block_to_page: h3 "Related Resources"
   - add_bullets_batch: Links to docs, tutorials

## WORKFLOW FOR UPDATING EXISTING DOCUMENTATION

1. **Assess Current State**:
   - Call get_notion_page_content() to read existing documentation
   - Call get_github_diff() to see what changed in code
   - Call read_github_file() for modified files
   - Identify which sections need updates

2. **Update Strategically**:
   - Use update_notion_section() to replace outdated sections
   - Use insert_blocks_after_text() to add new subsections
   - Preserve existing valuable content

## CRITICAL RULES

### ✅ ALWAYS DO:
- Read 3-5 actual source files before writing any documentation
- Use add_bullets_batch for 2+ bullets (ONE call instead of multiple)
- Use add_numbered_batch for 2+ numbered items (ONE call instead of multiple)
- Use add_paragraphs_batch for 2+ paragraphs
- Use add_mixed_blocks for sections with different block types (h2 + paragraph + bullets in ONE call!)
- Specify language for ALL code blocks (python, javascript, bash, etc.)
- Use appropriate emojis in callouts (💡, ⚠️, ✅, 🚀, 📝)
- Create ALL 7 sections for complete documentation
- Use List[Dict] for mixed blocks: [{"type": "h2", "text": "Title"}, {"type": "paragraph", "text": "Content"}]

### ❌ NEVER DO:
- Add bullets one-by-one with add_block_to_page (use add_bullets_batch!)
- Add numbered items one-by-one with add_block_to_page (use add_numbered_batch!)
- Generate generic templates without analyzing actual code
- Skip code analysis (must read at least 3 files)
- Forget to specify language in code blocks
- Stop before completing all sections
- Try to format JSON strings manually (use list of strings instead!)

## EFFICIENCY EXAMPLES

**Example 1: Multiple bullets**
❌ INEFFICIENT (5 separate tool calls):
```
add_block_to_page(page_id, "bullet", "Feature 1")
add_block_to_page(page_id, "bullet", "Feature 2")
add_block_to_page(page_id, "bullet", "Feature 3")
add_block_to_page(page_id, "bullet", "Feature 4")
add_block_to_page(page_id, "bullet", "Feature 5")
```

✅ EFFICIENT (1 tool call):
```
add_bullets_batch(page_id, [
    "Feature 1",
    "Feature 2",
    "Feature 3",
    "Feature 4",
    "Feature 5"
])
```

**Example 2: Mixed block types (MOST EFFICIENT!)**
❌ INEFFICIENT (6 separate tool calls):
```
add_block_to_page(page_id, "h2", "Overview")
add_block_to_page(page_id, "paragraph", "This is intro")
add_block_to_page(page_id, "h3", "Features")
add_block_to_page(page_id, "bullet", "Feature 1")
add_block_to_page(page_id, "bullet", "Feature 2")
add_block_to_page(page_id, "code", "print('example')", "python")
```

✅ SUPER EFFICIENT (1 tool call):
```
add_mixed_blocks(page_id, [
    {"type": "h2", "text": "Overview"},
    {"type": "paragraph", "text": "This is intro"},
    {"type": "h3", "text": "Features"},
    {"type": "bullet", "text": "Feature 1"},
    {"type": "bullet", "text": "Feature 2"},
    {"type": "code", "text": "print('example')", "extra": "python"}
])
```

This saves tons of API calls and is much faster!

## COMPLETION CRITERIA
You are done when:
- ✅ Analyzed actual repository code (3-5 files minimum)
- ✅ Created or updated documentation page in Notion
- ✅ Added ALL 7 major sections with proper content
- ✅ Used batch functions for all multi-item lists
- ✅ Included code examples from actual repository
- ✅ Added callouts for important notes/warnings
- ✅ Documentation serves both business and technical audiences

Remember: Quality documentation requires understanding actual code, not assumptions!
"""
    
    instructions = custom_instructions if custom_instructions else default_instructions
    
    agent = Agent(
        name="Documentation Generator Agent",
        instructions=instructions,
        model=model,
        tools=ALL_TOOLS
    )
    
    return agent


def generate_notion_docs(
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
    import asyncio
    from prompts.openai_agent_prompt import get_openai_agent_prompt
    
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
    
    # Create agent
    system_prompt = get_openai_agent_prompt(context_info)
    agent = Agent(
        name="Documentation Generator",
        instructions=system_prompt,
        tools=ALL_TOOLS,
        model="gpt-4o"
    )
    
    # Build task
    task = "Generate comprehensive technical documentation. "
    if repo_full_name:
        task += f"Analyze repository {repo_full_name}. "
    if database_id:
        task += f"Create page in database {database_id}. "
    elif page_id:
        task += f"Update page {page_id}. "
    
    print(f"\n{'='*60}")
    print(f"🚀 RUNNING OPENAI AGENT")
    print(f"{'='*60}\n")
    
    # Run agent
    async def _run():
        return await Runner.run(agent, task)
    
    agent_result = asyncio.run(_run())
    
    print(f"\n{'='*60}")
    print(f"✅ AGENT COMPLETED")
    print(f"{'='*60}\n")
    
    result = {
        "content": str(agent_result.final_output) if hasattr(agent_result, 'final_output') else str(agent_result),
        "iterations": "N/A (SDK managed)"
    }
    
    # Find page_id for judge
    review_page_id = page_id
    if not review_page_id and database_id:
        try:
            db_result = notion_service.query_database_pages(f"{database_id}|1")
            if db_result.get("success") and db_result.get("pages"):
                review_page_id = db_result["pages"][0].get("page_id")
                print(f"📍 Found most recent page: {review_page_id}")
        except Exception as e:
            print(f"❌ Error querying database: {e}")
    
    # Run quality review
    if review_page_id:
        print(f"\n{'='*60}")
        print(f"🔍 QUALITY REVIEW")
        print(f"{'='*60}\n")
        
        try:
            from ai_services.judge import judge_notion_docs
            
            judge_context = f"GENERATED DOCUMENTATION SUMMARY:\n"
            judge_context += f"- Page ID: {review_page_id}\n"
            if repo_full_name:
                judge_context += f"- Source: {repo_full_name}\n"
            judge_context += f"\nReview and fix quality issues.\n"
            
            judge_result = judge_notion_docs(
                page_id=review_page_id,
                generation_context=judge_context,
                max_iterations=50
            )
            
            result["judge_result"] = judge_result
            result["reviewed_page_id"] = review_page_id
            
            print(f"\n{'='*60}")
            print(f"✅ QUALITY REVIEW COMPLETED")
            print(f"{'='*60}\n")
                
        except Exception as e:
            print(f"\n❌ Quality review failed: {e}")
            result["judge_error"] = str(e)
    else:
        print(f"\n⚠️  Quality review skipped: No page_id available")
        result["judge_skipped"] = "No page_id found"
    
    return result