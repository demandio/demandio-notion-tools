from typing import Optional
from google.cloud import secretmanager
import re
from urllib.parse import urlparse, parse_qs

def get_secret(secret_name: str, project_id: str) -> str:
    """
    Fetch a secret from Google Cloud Secret Manager.
    
    Args:
        secret_name: Name of the secret to fetch
        project_id: Google Cloud project ID
        
    Returns:
        The secret value as a string
    """
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

def parse_notion_url(url: str) -> Optional[str]:
    """
    Extract the page ID from a Notion URL.
    
    Args:
        url: Notion page URL
        
    Returns:
        The page ID if found, None otherwise
        
    Examples:
        >>> url = "https://www.notion.so/workspace/c2eb1241ebbf4f39acc1ac716dae03f7"
        >>> parse_notion_url(url)
        'c2eb1241ebbf4f39acc1ac716dae03f7'
    """
    # Try to extract UUID using regex
    uuid_pattern = r"[a-f0-9]{32}"
    match = re.search(uuid_pattern, url)
    if match:
        return match.group(0)
    
    # If no UUID found, try parsing the URL
    parsed = urlparse(url)
    path_parts = parsed.path.split("/")
    
    # Look for UUID in path parts
    for part in path_parts:
        if re.match(uuid_pattern, part):
            return part
            
    # Check query parameters
    query_params = parse_qs(parsed.query)
    for param in query_params.values():
        for value in param:
            if re.match(uuid_pattern, value):
                return value
                
    return None

def construct_notion_block_url(page_id: str, block_id: str) -> str:
    """
    Construct a deep link URL to a specific Notion block.
    
    Args:
        page_id: Notion page ID
        block_id: Block ID within the page
        
    Returns:
        Direct URL to the specific block
    """
    clean_page_id = page_id.replace("-", "")
    clean_block_id = block_id.replace("-", "")
    return f"https://www.notion.so/{clean_page_id}#{clean_block_id}" 