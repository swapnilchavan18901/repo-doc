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

    def search_page_by_title(self, input_str: str) -> Dict[str, Any]:
        """Search for a page by title. Format: 'page_title'"""
        try:
            page_title = input_str.strip()
            url = f"{self.base_url}/search"
            
            payload = {
                "query": page_title,
                "filter": {
                    "property": "object",
                    "value": "page"
                },
                "page_size": 10
            }
            
            res = requests.post(url, headers=self.headers, json=payload)
            
            if res.status_code != 200:
                return {"success": False, "error": res.text}
            
            results = res.json().get("results", [])
            
            # Find exact match
            for page in results:
                title = ""
                if page.get("properties"):
                    for prop_name, prop_value in page["properties"].items():
                        if prop_value.get("type") == "title":
                            title_array = prop_value.get("title", [])
                            if title_array:
                                title = title_array[0].get("text", {}).get("content", "")
                                break
                
                if title.lower() == page_title.lower():
                    return {
                        "success": True,
                        "found": True,
                        "page_id": page["id"],
                        "title": title,
                        "url": page.get("url", "")
                    }
            
            return {
                "success": True,
                "found": False,
                "message": f"No page found with title '{page_title}'"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_all_databases(self, input_str: str = "") -> Dict[str, Any]:
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

    def create_doc_page(self, input_str: str) -> Dict[str, Any]:
        """Create documentation page. Format: 'database_id|page_title'"""
        try:
            if '|' not in input_str:
                return {"success": False, "error": "Input must be in format 'database_id|page_title'"}
            
            database_id, title = input_str.split('|', 1)
            database_id = database_id.strip()
            title = title.strip()
        except Exception as e:
            return {"success": False, "error": f"Failed to parse input: {str(e)}", "input": input_str}
        
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

    def append_blocks(self, input_str: str) -> Dict[str, Any]:
        """Append blocks to page. Format: 'page_id|blocks_json'"""
        try:
            if '|' not in input_str:
                return {"success": False, "error": "Input must be in format 'page_id|blocks_json'"}
            
            page_id, blocks_json = input_str.split('|', 1)
            page_id = page_id.strip()
            blocks = json.loads(blocks_json)
        except json.JSONDecodeError:
            return {"success": False, "error": "Invalid JSON format for blocks"}
        except Exception as e:
            return {"success": False, "error": f"Failed to parse input: {str(e)}", "input": input_str}
        
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

    def replace_section(self, input_str: str) -> Dict[str, Any]:
        """Replace section. Format: 'page_id|heading_text|content_blocks_json'"""
        try:
            parts = input_str.split('|', 2)
            if len(parts) != 3:
                return {"success": False, "error": "Input must be in format 'page_id|heading_text|content_blocks_json'"}
            
            page_id, heading_text, content_json = parts
            page_id = page_id.strip()
            heading_text = heading_text.strip()
            new_blocks = json.loads(content_json)
        except json.JSONDecodeError:
            return {"success": False, "error": "Invalid JSON format for content blocks"}
        except Exception as e:
            return {"success": False, "error": f"Failed to parse input: {str(e)}", "input": input_str}
        
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
    
    def get_page_content(self, input_str: str) -> Dict[str, Any]:
        """Get content from a Notion page with block structure. Format: 'page_id'"""
        try:
            page_id = input_str.strip()
            blocks = self.get_page_blocks(page_id)
            
            content_sections = []
            section_count = 0
            
            for i, block in enumerate(blocks):
                block_type = block["type"]
                
                if block_type.startswith("heading"):
                    section_count += 1
                    text = self._get_block_text(block)
                    content_sections.append({
                        "section": section_count,
                        "type": block_type,
                        "text": text,
                        "block_id": block["id"]
                    })
                elif block_type in ["paragraph", "bulleted_list_item", "numbered_list_item"]:
                    text = self._get_block_text(block)
                    if text.strip():
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
            return {"success": False, "error": str(e), "page_id": input_str}
    
    def create_blocks(self, input_str: str) -> Dict[str, Any]:
        """Create Notion blocks from text. Format: 'block_type|text' or 'block_type|text|extra_param'"""
        try:
            if '|' not in input_str:
                return {"success": False, "error": "Input must be in format 'block_type|text' or 'block_type|text|extra_param'"}
            
            parts = input_str.split('|')
            block_type = parts[0].strip().lower()
            
            if block_type == "h1":
                block = self.h1(parts[1].strip())
            elif block_type == "h2":
                block = self.h2(parts[1].strip())
            elif block_type == "h3":
                block = self.h3(parts[1].strip())
            elif block_type == "paragraph":
                block = self.paragraph(parts[1].strip())
            elif block_type == "bullet":
                block = self.bullet(parts[1].strip())
            elif block_type == "numbered":
                block = self.numbered(parts[1].strip())
            elif block_type == "quote":
                block = self.quote(parts[1].strip())
            elif block_type == "code":
                code_content = parts[1].strip()
                language = parts[2].strip() if len(parts) > 2 else "python"
                block = self.code(code_content, language)
            elif block_type == "callout":
                text = parts[1].strip()
                emoji = parts[2].strip() if len(parts) > 2 else "💡"
                block = self.callout(text, emoji)
            elif block_type == "todo" or block_type == "to_do":
                text = parts[1].strip()
                checked = parts[2].strip().lower() == "true" if len(parts) > 2 else False
                block = self.to_do(text, checked)
            elif block_type == "toggle":
                summary = parts[1].strip()
                children = None
                if len(parts) > 2:
                    try:
                        children = json.loads(parts[2])
                    except json.JSONDecodeError:
                        return {"success": False, "error": "Invalid JSON for toggle children"}
                block = self.toggle(summary, children)
            elif block_type == "divider":
                block = self.divider()
            elif block_type == "toc" or block_type == "table_of_contents":
                block = self.table_of_contents()
            elif block_type == "mixed":
                try:
                    return {"success": True, "blocks": json.loads(parts[1])}
                except json.JSONDecodeError:
                    return {"success": False, "error": "Invalid JSON for mixed blocks"}
            else:
                return {"success": False, "error": f"Unsupported block type: {block_type}"}
            
            return {"success": True, "block": block}
        except Exception as e:
            return {"success": False, "error": str(e), "input": input_str}

    def insert_after_block(self, input_str: str) -> Dict[str, Any]:
        """Insert blocks after block ID. Format: 'block_id|blocks_json'"""
        try:
            if '|' not in input_str:
                return {"success": False, "error": "Input must be in format 'block_id|blocks_json'"}
            
            after_block_id, blocks_json = input_str.split('|', 1)
            after_block_id = after_block_id.strip()
            new_blocks = json.loads(blocks_json)
        except json.JSONDecodeError:
            return {"success": False, "error": "Invalid JSON format for blocks"}
        except Exception as e:
            return {"success": False, "error": f"Failed to parse input: {str(e)}", "input": input_str}
        
        res = requests.patch(
            f"{self.base_url}/blocks/{after_block_id}/children",
            headers=self.headers,
            json={"children": new_blocks}
        )

        if res.status_code != 200:
            return {"success": False, "error": res.text}

        return {
            "success": True,
            "inserted_blocks": len(new_blocks)
        }

    def insert_between_by_text(self, input_str: str) -> Dict[str, Any]:
        """Insert blocks after text. Format: 'page_id|after_text|blocks_json'"""
        try:
            parts = input_str.split('|', 2)
            if len(parts) != 3:
                return {"success": False, "error": "Input must be in format 'page_id|after_text|blocks_json'"}
            
            page_id, after_text, blocks_json = parts
            page_id = page_id.strip()
            after_text = after_text.strip()
            new_blocks = json.loads(blocks_json)
        except json.JSONDecodeError:
            return {"success": False, "error": "Invalid JSON format for blocks"}
        except Exception as e:
            return {"success": False, "error": f"Failed to parse input: {str(e)}", "input": input_str}
        
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

        block_input = f"{target_block['id']}|{blocks_json}"
        return self.insert_after_block(block_input)

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
