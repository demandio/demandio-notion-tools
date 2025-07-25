from typing import List, Dict, Optional
from notion_client import Client
from notion_client.errors import APIResponseError

class NotionClient:
    def __init__(self, token: str):
        """
        Initialize the Notion client.
        
        Args:
            token: Notion API token
        """
        self.client = Client(auth=token)
        
    def get_page_owner_email(self, page_id: str) -> Optional[str]:
        """
        Fetch the email address of the page owner from the "Owner" property.
        
        Args:
            page_id: Notion page ID
            
        Returns:
            Owner's email address if found, None otherwise
        """
        try:
            page = self.client.pages.retrieve(page_id=page_id)
            
            # Look for the "Owner" property in the page properties
            properties = page.get("properties", {})
            owner_prop = properties.get("Owner")
            
            if owner_prop and owner_prop["type"] == "people":
                people = owner_prop.get("people", [])
                if people:
                    return people[0].get("person", {}).get("email")
                    
        except APIResponseError as e:
            print(f"Error fetching page owner for {page_id}: {e}")
            
        return None
        
    def get_page_blocks(self, page_id: str) -> List[Dict]:
        """
        Retrieve all blocks from a Notion page and return them in a simplified format.
        
        Args:
            page_id: Notion page ID
            
        Returns:
            List of dictionaries containing block IDs and their text content
        """
        blocks = []
        
        try:
            # Fetch all blocks using pagination
            has_more = True
            start_cursor = None
            
            while has_more:
                response = self.client.blocks.children.list(
                    block_id=page_id,
                    start_cursor=start_cursor
                )
                
                for block in response["results"]:
                    # Extract text content based on block type
                    content = self._extract_block_text(block)
                    if content:
                        blocks.append({
                            "id": block["id"],
                            "content": content,
                            "type": block["type"]
                        })
                        
                has_more = response["has_more"]
                start_cursor = response.get("next_cursor")
                
        except APIResponseError as e:
            print(f"Error fetching blocks for page {page_id}: {e}")
            
        return blocks
        
    def _extract_block_text(self, block: Dict) -> Optional[str]:
        """
        Extract plain text content from a Notion block.
        
        Args:
            block: Notion block object
            
        Returns:
            Plain text content if available, None otherwise
        """
        block_type = block["type"]
        
        # Handle different block types
        if block_type in ["paragraph", "heading_1", "heading_2", "heading_3", "bulleted_list_item", "numbered_list_item"]:
            rich_text = block[block_type].get("rich_text", [])
            return "".join(text.get("plain_text", "") for text in rich_text)
            
        elif block_type == "table":
            # For tables, include a structured representation
            rows = []
            for row in block.get("table", {}).get("rows", []):
                cells = []
                for cell in row.get("cells", []):
                    cell_text = "".join(text.get("plain_text", "") for text in cell)
                    cells.append(cell_text)
                rows.append(" | ".join(cells))
            return "\n".join(rows)
            
        elif block_type == "code":
            # For code blocks, include the language
            code = block["code"]
            language = code.get("language", "")
            text = "".join(text.get("plain_text", "") for text in code.get("rich_text", []))
            return f"```{language}\n{text}\n```"
            
        return None 