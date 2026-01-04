"""
Example usage of OpenAI Agents SDK for Notion documentation generation.
"""

from agents_sdk.openai_sdk import generate_notion_docs

# Simple usage - just like the original function!
result = generate_notion_docs(
    repo_full_name="owner/repo",
    before_sha="abc123",
    after_sha="def456",
    database_id="your-notion-database-id"
)

print(result)
