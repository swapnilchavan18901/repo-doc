import requests
import json
import re
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
    
    def _is_valid_uuid(self, uuid_str: str) -> bool:
        """Check if a string contains a valid UUID format (with or without hyphens, with or without prefix)"""
        if not uuid_str or not isinstance(uuid_str, str):
            return False
        
        # Check for placeholder values first
        if uuid_str.upper() in ['TO_FILL', 'PLACEHOLDER', 'NONE', 'NULL', '']:
            return False
        
        # Remove hyphens and look for a 32-character hex string (UUID)
        # This handles prefixes like "DocDelta-ReadMe-2d322f89689b8005a4e8c224ae074ddd"
        uuid_clean = uuid_str.replace('-', '')
        uuid_pattern = re.compile(r'[0-9a-f]{32}', re.IGNORECASE)
        match = uuid_pattern.search(uuid_clean)
        
        # Must find exactly 32 hex characters
        return bool(match and len(match.group(0)) == 32)
    
    def _normalize_uuid(self, uuid_str: str) -> str:
        """Normalize UUID format for Notion API (extracts UUID and ensures proper format with hyphens)"""
        if not uuid_str:
            return uuid_str
        
        # Remove hyphens and extract the 32-character hex UUID
        # This handles prefixes like "DocDelta-ReadMe-2d322f89689b8005a4e8c224ae074ddd"
        uuid_clean = uuid_str.replace('-', '')
        uuid_pattern = re.compile(r'[0-9a-f]{32}', re.IGNORECASE)
        match = uuid_pattern.search(uuid_clean)
        
        if not match:
            return uuid_str  # Return original if no UUID found
        
        uuid_clean = match.group(0)
        
        # Format with hyphens in standard format: 8-4-4-4-12
        return f"{uuid_clean[0:8]}-{uuid_clean[8:12]}-{uuid_clean[12:16]}-{uuid_clean[16:20]}-{uuid_clean[20:32]}"

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
        # Validate database_id before making API call
        if not self._is_valid_uuid(database_id):
            error_msg = f"Invalid database ID format: {database_id}. Must be a valid UUID."
            print(f"SCHEMA STATUS: 400 (validation)")
            print(f"SCHEMA RAW: {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
        
        # Normalize UUID (remove hyphens if present)
        normalized_id = self._normalize_uuid(database_id)
        url = f"{self.base_url}/databases/{normalized_id}"

        res = requests.get(url, headers=self.headers)

        print("SCHEMA STATUS:", res.status_code)
        if res.status_code != 200:
            # Only print full error in debug mode or if it's not a 404
            if res.status_code == 404:
                print(f"SCHEMA RAW: Database not found or not accessible: {database_id}")
            else:
                print("SCHEMA RAW:", res.text)

        if res.status_code != 200:
            return {
                "success": False,
                "error": res.text,
                "status_code": res.status_code
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
    
    def query_database_pages(self, input_str: str) -> Dict[str, Any]:
        """Query pages from database. Format: 'database_id' or 'database_id|page_size'"""
        try:
            parts = input_str.split('|')
            database_id = parts[0].strip()
            page_size = int(parts[1]) if len(parts) > 1 else 10
        except Exception as e:
            return {"success": False, "error": f"Failed to parse input: {str(e)}", "input": input_str}
        
        # Validate database_id before making API call
        if not self._is_valid_uuid(database_id):
            error_msg = f"Invalid database ID format: {database_id}. Must be a valid UUID."
            print(f"QUERY DATABASE STATUS: 400 (validation)")
            print(f"QUERY DATABASE RAW: {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
        
        # Normalize UUID (remove hyphens if present)
        normalized_id = self._normalize_uuid(database_id)
        url = f"{self.base_url}/databases/{normalized_id}/query"
        
        payload = {
            "page_size": page_size,
            "sorts": [
                {
                    "timestamp": "created_time",
                    "direction": "descending"
                }
            ]
        }
        
        res = requests.post(url, headers=self.headers, json=payload)
        
        print("QUERY DATABASE STATUS:", res.status_code)
        if res.status_code != 200:
            # Only print full error in debug mode or if it's not a 404
            if res.status_code == 404:
                print(f"QUERY DATABASE RAW: Database not found or not accessible: {database_id}")
            else:
                print("QUERY DATABASE RAW:", res.text)
        else:
            print("QUERY DATABASE RAW:", res.text)
        
        if res.status_code != 200:
            return {
                "success": False,
                "error": res.text,
                "status_code": res.status_code
            }
        
        data = res.json()
        pages = []
        
        for page in data.get("results", []):
            page_id = page["id"]
            title = ""
            
            # Extract title from properties
            if page.get("properties"):
                for prop_name, prop_value in page["properties"].items():
                    if prop_value.get("type") == "title":
                        title_array = prop_value.get("title", [])
                        if title_array:
                            title = title_array[0].get("text", {}).get("content", "")
                            break
            
            pages.append({
                "page_id": page_id,
                "title": title,
                "url": page.get("url", ""),
                "created_time": page.get("created_time", "")
            })
        
        return {
            "success": True,
            "database_id": database_id,
            "count": len(pages),
            "pages": pages
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
        
        # Validate database_id before proceeding
        if not self._is_valid_uuid(database_id):
            return {
                "success": False,
                "error": f"Invalid database ID format: {database_id}. Must be a valid UUID."
            }
        
        # Step 1: get schema to resolve title key
        schema = self.get_database_schema(database_id)

        if not schema.get("success"):
            # If it's a 404, provide a more helpful error message
            if schema.get("status_code") == 404:
                return {
                    "success": False,
                    "error": f"Database not found or not accessible. Make sure the database ID is correct and the integration has access to it.",
                    "database_id": database_id,
                    "details": schema
                }
            return {
                "success": False,
                "error": "Failed to resolve database schema",
                "details": schema
            }

        title_key = schema["title_key"]
        
        # Normalize database_id for API call
        normalized_db_id = self._normalize_uuid(database_id)

        payload = {
            "parent": {
                "database_id": normalized_db_id
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
        """Append blocks. Format: 'page_id|blocks_json' or 'page_id|single_block_json'"""
        try:
            if '|' not in input_str:
                return {"success": False, "error": "Input must be in format 'page_id|blocks_json' or 'page_id|single_block_json'"}
            
            page_id, blocks_json = input_str.split('|', 1)
            page_id = page_id.strip()
            
            # Validate page_id before making API call
            if not self._is_valid_uuid(page_id):
                error_msg = f"Invalid page ID format: '{page_id}'. Must be a valid UUID. If you see 'TO_FILL', the page was not created successfully."
                print(f"APPEND BLOCKS STATUS: 400 (validation)")
                print(f"APPEND BLOCKS RAW: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg
                }
            
            blocks_data = json.loads(blocks_json)
            
            # Support both single block and array of blocks
            if isinstance(blocks_data, dict):
                blocks = [blocks_data]  # Wrap single block in array
            else:
                blocks = blocks_data
        except json.JSONDecodeError:
            return {"success": False, "error": "Invalid JSON format for blocks"}
        except Exception as e:
            return {"success": False, "error": f"Failed to parse input: {str(e)}", "input": input_str}
        
        # Normalize page_id for API call
        normalized_page_id = self._normalize_uuid(page_id)
        url = f"{self.base_url}/blocks/{normalized_page_id}/children"

        payload = {
            "children": blocks
        }

        res = requests.patch(url, headers=self.headers, json=payload)

        print("APPEND BLOCKS STATUS:", res.status_code)
        if res.status_code != 200:
            print("APPEND BLOCKS RAW:", res.text)
        else:
            # Only print on success if needed for debugging
            pass

        if res.status_code != 200:
            return {
                "success": False,
                "error": res.text,
                "status_code": res.status_code
            }

        return {
            "success": True,
            "blocks_added": len(blocks)
        }
  
    def get_page_blocks(self, page_id: str) -> List[Dict[str, Any]]:
        # Validate page_id
        if not self._is_valid_uuid(page_id):
            raise ValueError(f"Invalid page ID format: {page_id}. Must be a valid UUID.")
        
        # Normalize page_id for API call
        normalized_page_id = self._normalize_uuid(page_id)
        res = requests.get(
            f"{self.base_url}/blocks/{normalized_page_id}/children",
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
            
            # Validate page_id before proceeding
            if not self._is_valid_uuid(page_id):
                return {
                    "success": False,
                    "error": f"Invalid page ID format: '{page_id}'. Must be a valid UUID."
                }
            
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
            normalized_block_id = self._normalize_uuid(block['id'])
            requests.delete(
                f"{self.base_url}/blocks/{normalized_block_id}",
                headers=self.headers
            )

        # Insert new blocks after heading as siblings (not children)
        heading_block_id = blocks[start_index]["id"]
        
        # Normalize IDs for API call
        normalized_page_id = self._normalize_uuid(page_id)
        normalized_heading_id = self._normalize_uuid(heading_block_id)

        # FIX: Use 'after' parameter to insert blocks as SIBLINGS after the heading
        payload = {
            "children": new_blocks,
            "after": normalized_heading_id  # Insert AFTER heading as sibling, not as child
        }

        res = requests.patch(
            f"{self.base_url}/blocks/{normalized_page_id}/children",
            headers=self.headers,
            json=payload
        )

        if res.status_code != 200:
            return {
                "success": False,
                "error": res.text,
                "status_code": res.status_code
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
            
            # Validate page_id before proceeding
            if not self._is_valid_uuid(page_id):
                return {
                    "success": False,
                    "error": f"Invalid page ID format: '{page_id}'. Must be a valid UUID.",
                    "page_id": page_id
                }
            
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
    
    def add_block_to_page(self, input_str: str) -> Dict[str, Any]:
        """Create and append a block to page in one step. Format: 'page_id|block_type|text' or 'page_id|block_type|text|extra_param'"""
        try:
            if '|' not in input_str:
                return {"success": False, "error": "Input must be in format 'page_id|block_type|text'"}
            
            parts = input_str.split('|', 1)
            page_id = parts[0].strip()
            
            # Validate page_id before proceeding
            if not self._is_valid_uuid(page_id):
                return {
                    "success": False,
                    "error": f"Invalid page ID format: '{page_id}'. Must be a valid UUID. If you see 'TO_FILL', the page was not created successfully."
                }
            
            block_input = parts[1]
            
            block_result = self.create_blocks(block_input)
            
            if not block_result.get("success"):
                return block_result
            
            block = block_result.get("block")
            if not block:
                return {"success": False, "error": "No block created"}
            
            block_json = json.dumps(block)
            append_result = self.append_blocks(f"{page_id}|{block_json}")
            
            if append_result.get("success"):
                return {
                    "success": True,
                    "message": f"Added {block['type']} to page",
                    "block_type": block['type']
                }
            else:
                return append_result
        except Exception as e:
            return {"success": False, "error": str(e), "input": input_str}
    
    def add_bullets_batch(self, input_str: str) -> Dict[str, Any]:
        """Add multiple bullet points at once. Format: 'page_id|bullet1##bullet2##bullet3' (use ## as separator)"""
        try:
            if '|' not in input_str:
                return {"success": False, "error": "Input must be in format 'page_id|bullet1##bullet2##bullet3'"}
            
            page_id, bullets_str = input_str.split('|', 1)
            page_id = page_id.strip()
            
            # Validate page_id before proceeding
            if not self._is_valid_uuid(page_id):
                return {
                    "success": False,
                    "error": f"Invalid page ID format: '{page_id}'. Must be a valid UUID."
                }
            
            # Split by ## separator
            bullet_texts = [b.strip() for b in bullets_str.split('##') if b.strip()]
            
            if not bullet_texts:
                return {"success": False, "error": "No bullet points provided"}
            
            # Create all bullet blocks
            blocks = [self.bullet(text) for text in bullet_texts]
            
            # Send all at once
            blocks_json = json.dumps(blocks)
            result = self.append_blocks(f"{page_id}|{blocks_json}")
            
            if result.get("success"):
                return {
                    "success": True,
                    "message": f"Added {len(bullet_texts)} bullet points to page",
                    "blocks_added": len(bullet_texts)
                }
            else:
                return result
        except Exception as e:
            return {"success": False, "error": str(e), "input": input_str}
    
    def add_numbered_batch(self, input_str: str) -> Dict[str, Any]:
        """Add multiple numbered items at once. Format: 'page_id|item1##item2##item3' (use ## as separator)"""
        try:
            if '|' not in input_str:
                return {"success": False, "error": "Input must be in format 'page_id|item1##item2##item3'"}
            
            page_id, items_str = input_str.split('|', 1)
            page_id = page_id.strip()
            
            # Validate page_id before proceeding
            if not self._is_valid_uuid(page_id):
                return {
                    "success": False,
                    "error": f"Invalid page ID format: '{page_id}'. Must be a valid UUID."
                }
            
            # Split by ## separator
            item_texts = [i.strip() for i in items_str.split('##') if i.strip()]
            
            if not item_texts:
                return {"success": False, "error": "No numbered items provided"}
            
            # Create all numbered blocks
            blocks = [self.numbered(text) for text in item_texts]
            
            # Send all at once
            blocks_json = json.dumps(blocks)
            result = self.append_blocks(f"{page_id}|{blocks_json}")
            
            if result.get("success"):
                return {
                    "success": True,
                    "message": f"Added {len(item_texts)} numbered items to page",
                    "blocks_added": len(item_texts)
                }
            else:
                return result
        except Exception as e:
            return {"success": False, "error": str(e), "input": input_str}
    
    def add_paragraphs_batch(self, input_str: str) -> Dict[str, Any]:
        """Add multiple paragraphs at once. Format: 'page_id|para1##para2##para3' (use ## as separator)"""
        try:
            if '|' not in input_str:
                return {"success": False, "error": "Input must be in format 'page_id|para1##para2##para3'"}
            
            page_id, paras_str = input_str.split('|', 1)
            page_id = page_id.strip()
            
            # Validate page_id before proceeding
            if not self._is_valid_uuid(page_id):
                return {
                    "success": False,
                    "error": f"Invalid page ID format: '{page_id}'. Must be a valid UUID."
                }
            
            # Split by ## separator
            para_texts = [p.strip() for p in paras_str.split('##') if p.strip()]
            
            if not para_texts:
                return {"success": False, "error": "No paragraphs provided"}
            
            # Create all paragraph blocks
            blocks = [self.paragraph(text) for text in para_texts]
            
            # Send all at once
            blocks_json = json.dumps(blocks)
            result = self.append_blocks(f"{page_id}|{blocks_json}")
            
            if result.get("success"):
                return {
                    "success": True,
                    "message": f"Added {len(para_texts)} paragraphs to page",
                    "blocks_added": len(para_texts)
                }
            else:
                return result
        except Exception as e:
            return {"success": False, "error": str(e), "input": input_str}

    def insert_after_block(self, input_str: str) -> Dict[str, Any]:
        """
        Insert blocks after block ID. Format: 'parent_id|after_block_id|blocks_json'
        
        IMPORTANT: This inserts blocks as SIBLINGS after the target block.
        The parent_id is typically the page_id for top-level blocks.
        """
        try:
            parts = input_str.split('|', 2)
            if len(parts) != 3:
                return {"success": False, "error": "Input must be in format 'parent_id|after_block_id|blocks_json'"}
            
            parent_id, after_block_id, blocks_json = parts
            parent_id = parent_id.strip()
            after_block_id = after_block_id.strip()
            
            # Validate IDs before proceeding
            if not self._is_valid_uuid(parent_id):
                return {
                    "success": False,
                    "error": f"Invalid parent ID format: '{parent_id}'. Must be a valid UUID."
                }
            if not self._is_valid_uuid(after_block_id):
                return {
                    "success": False,
                    "error": f"Invalid block ID format: '{after_block_id}'. Must be a valid UUID."
                }
            
            new_blocks = json.loads(blocks_json)
        except json.JSONDecodeError:
            return {"success": False, "error": "Invalid JSON format for blocks"}
        except Exception as e:
            return {"success": False, "error": f"Failed to parse input: {str(e)}", "input": input_str}
        
        # Normalize IDs for API call
        normalized_parent_id = self._normalize_uuid(parent_id)
        normalized_after_id = self._normalize_uuid(after_block_id)
        # FIX: Use parent's children endpoint with 'after' parameter
        res = requests.patch(
            f"{self.base_url}/blocks/{normalized_parent_id}/children",
            headers=self.headers,
            json={
                "children": new_blocks,
                "after": normalized_after_id  # Insert AFTER this block as sibling
            }
        )

        if res.status_code != 200:
            return {
                "success": False,
                "error": res.text,
                "status_code": res.status_code
            }

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
            
            # Validate page_id before proceeding
            if not self._is_valid_uuid(page_id):
                return {
                    "success": False,
                    "error": f"Invalid page ID format: '{page_id}'. Must be a valid UUID."
                }
            
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

        # FIX: Use the 'after' parameter to insert blocks as SIBLINGS, not children
        # Insert after the target block by appending to the page with 'after' parameter
        normalized_page_id = self._normalize_uuid(page_id)
        normalized_target_block_id = self._normalize_uuid(target_block['id'])
        
        res = requests.patch(
            f"{self.base_url}/blocks/{normalized_page_id}/children",
            headers=self.headers,
            json={
                "children": new_blocks,
                "after": normalized_target_block_id  # Insert AFTER this block as sibling
            }
        )

        if res.status_code != 200:
            return {
                "success": False,
                "error": res.text,
                "status_code": res.status_code
            }

        return {
            "success": True,
            "inserted_blocks": len(new_blocks),
            "inserted_after": after_text
        }

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
