import requests
import json
from typing import Dict, List, Optional, Any
from env import NOTION_API_KEY, NOTION_DATABASE_ID

class NotionService:

    def __init__(self):
        self.api_key = NOTION_API_KEY
        self.database_id = NOTION_DATABASE_ID

        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }

    def get_all_databases(self) -> Dict[str, Any]:
        url = f"{self.base_url}/search"

        payload = {
            "filter": {
                "property": "object",
                "value": "database"
            },
            "page_size": 100
        }

        res = requests.post(url, headers=self.headers, json=payload)

        print("STATUS:", res.status_code)
        print("RAW:", res.text)

        if res.status_code != 200:
            return {
                "success": False,
                "error": res.text
            }

        databases = []
        print(f"Res: {res.json()}")
        for db in res.json()["results"]:
            title = "Untitled"
            if db.get("title") and len(db["title"]) > 0:
                title = db["title"][0]["text"]["content"]

            databases.append({
                "id": db["id"],
                "title": title,
                "url": db["url"]
            })

        return {
            "success": True,
            "count": len(databases),
            "databases": databases
        }


    def get_database_schema(self, database_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/databases/{database_id}"

        res = requests.get(url, headers=self.headers)

        print("SCHEMA STATUS:", res.status_code)
        print("SCHEMA RAW:", res.text)

        if res.status_code != 200:
            return {
                "success": False,
                "error": res.text
            }

        data = res.json()
        title_key = None

        for key, prop in data["properties"].items():
            if prop["type"] == "title":
                title_key = key
                break

        if not title_key:
            return {
                "success": False,
                "error": "No title property found in database"
            }

        return {
            "success": True,
            "database_id": database_id,
            "database_name": data["title"][0]["text"]["content"] if data.get("title") else "Untitled",
            "title_key": title_key,
            "properties": list(data["properties"].keys())
        }

    def create_doc_page(self, database_id: str, title: str) -> Dict[str, Any]:
        # Step 1: get schema to resolve title key
        schema = self.get_database_schema(database_id)

        if not schema.get("success"):
            return {
                "success": False,
                "error": "Failed to resolve database schema",
                "details": schema
            }

        title_key = schema["title_key"]

        payload = {
            "parent": {
                "database_id": database_id
            },
            "properties": {
                title_key: {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                }
            }
        }

        res = requests.post(
            f"{self.base_url}/pages",
            headers=self.headers,
            json=payload
        )

        print("CREATE PAGE STATUS:", res.status_code)
        print("CREATE PAGE RAW:", res.text)

        if res.status_code != 200:
            return {
                "success": False,
                "error": "Failed to create page",
                "details": res.text
            }

        page = res.json()

        return {
            "success": True,
            "page_id": page["id"],
            "url": page["url"],
            "title": title
        }

    def append_blocks(self, page_id: str, blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        url = f"{self.base_url}/blocks/{page_id}/children"

        payload = {
            "children": blocks
        }

        res = requests.patch(url, headers=self.headers, json=payload)

        print("APPEND BLOCKS STATUS:", res.status_code)
        print("APPEND BLOCKS RAW:", res.text)

        if res.status_code != 200:
            return {
                "success": False,
                "error": res.text
            }

        return {
            "success": True,
            "blocks_added": len(blocks)
        }
  
    def get_page_blocks(self, page_id: str) -> List[Dict[str, Any]]:
        res = requests.get(
            f"{self.base_url}/blocks/{page_id}/children",
            headers=self.headers
        )

        if res.status_code != 200:
            raise Exception(res.text)

        return res.json()["results"]

    def replace_section(self,page_id: str,heading_text: str,new_blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        blocks = self.get_page_blocks(page_id)
        start_index = None
        end_index = None

        # Locate heading
        for i, block in enumerate(blocks):
            if block["type"].startswith("heading"):
                text = self._get_block_text(block)
                if text.strip() == heading_text:
                    start_index = i
                    break

        if start_index is None:
            return {
                "success": False,
                "error": f"Heading '{heading_text}' not found"
            }

        # Find end (next heading or end of page)
        for i in range(start_index + 1, len(blocks)):
            if blocks[i]["type"].startswith("heading"):
                end_index = i
                break

        if end_index is None:
            end_index = len(blocks)

        # Delete old section blocks (excluding heading)
        for block in blocks[start_index + 1:end_index]:
            requests.delete(
                f"{self.base_url}/blocks/{block['id']}",
                headers=self.headers
            )

        # Insert new blocks after heading
        heading_block_id = blocks[start_index]["id"]

        payload = {
            "children": new_blocks
        }

        res = requests.patch(
            f"{self.base_url}/blocks/{heading_block_id}/children",
            headers=self.headers,
            json=payload
        )

        if res.status_code != 200:
            return {
                "success": False,
                "error": res.text
            }

        return {
            "success": True,
            "section": heading_text,
            "replaced_blocks": len(new_blocks)
        }
        
    def _get_block_text(self, block: Dict[str, Any]) -> str:
        block_type = block["type"]
        rich_text = block[block_type].get("rich_text", [])
        return "".join(rt["text"]["content"] for rt in rich_text if rt["type"] == "text")

    def insert_after_block(
        self,
        after_block_id: str,
        new_blocks: list
    ):
        """
        Insert new blocks immediately after a given block
        """
        res = requests.patch(
            f"{self.base_url}/blocks/{after_block_id}/children",
            headers=self.headers,
            json={"children": new_blocks}
        )

        if res.status_code != 200:
            raise Exception(res.text)

        return {
            "success": True,
            "inserted_blocks": len(new_blocks)
        }

    def insert_between_by_text(
        self,
        page_id: str,
        after_text: str,
        new_blocks: list
    ):
        """
        Insert new blocks after the block whose text matches `after_text`
        """
        blocks = self.get_page_blocks(page_id)

        target_block = None
        for block in blocks:
            text = self._get_block_text(block).strip()
            if text == after_text:
                target_block = block
                break

        if not target_block:
            return {
                "success": False,
                "error": f"Block with text '{after_text}' not found"
            }

        return self.insert_after_block(
            after_block_id=target_block["id"],
            new_blocks=new_blocks
        )

    #block builder
    def h1(self, text: str) -> Dict[str, Any]:
        """Create a Heading 1 block"""
        return {
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            }
        }

    def h2(self, text: str) -> Dict[str, Any]:
        """Create a Heading 2 block"""
        return {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            }
        }

    def h3(self, text: str) -> Dict[str, Any]:
        """Create a Heading 3 block"""
        return {
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            }
        }

    def paragraph(self, text: str) -> Dict[str, Any]:
        """Create a paragraph block"""
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            }
        }

    def bullet(self, text: str) -> Dict[str, Any]:
        """Create a bulleted list item"""
        return {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            }
        }

    def numbered(self, text: str) -> Dict[str, Any]:
        """Create a numbered list item"""
        return {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            }
        }

    def code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Create a code block with syntax highlighting
        
        Args:
            code: The code content
            language: Programming language (e.g., 'python', 'javascript', 'java', 'sql', etc.)
        """
        return {
            "object": "block",
            "type": "code",
            "code": {
                "rich_text": [{"type": "text", "text": {"content": code}}],
                "language": language
            }
        }

    def quote(self, text: str) -> Dict[str, Any]:
        """Create a quote block"""
        return {
            "object": "block",
            "type": "quote",
            "quote": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            }
        }

    def callout(self, text: str, emoji: str = "💡") -> Dict[str, Any]:
        """Create a callout block with an emoji icon
        
        Args:
            text: The callout text
            emoji: Emoji icon (default: 💡)
        """
        return {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [{"type": "text", "text": {"content": text}}],
                "icon": {"type": "emoji", "emoji": emoji}
            }
        }

    def divider(self) -> Dict[str, Any]:
        """Create a horizontal divider"""
        return {
            "object": "block",
            "type": "divider",
            "divider": {}
        }

    def toggle(self, summary: str, children: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Create a toggle/collapsible block
        
        Args:
            summary: The toggle header text
            children: Optional list of child blocks to nest inside the toggle
        """
        block = {
            "object": "block",
            "type": "toggle",
            "toggle": {
                "rich_text": [{"type": "text", "text": {"content": summary}}]
            }
        }
        if children:
            block["toggle"]["children"] = children
        return block

    def to_do(self, text: str, checked: bool = False) -> Dict[str, Any]:
        """Create a to-do checkbox item
        
        Args:
            text: The to-do text
            checked: Whether the checkbox is checked (default: False)
        """
        return {
            "object": "block",
            "type": "to_do",
            "to_do": {
                "rich_text": [{"type": "text", "text": {"content": text}}],
                "checked": checked
            }
        }

    def table_of_contents(self) -> Dict[str, Any]:
        """Create an automatic table of contents block"""
        return {
            "object": "block",
            "type": "table_of_contents",
            "table_of_contents": {}
        }
