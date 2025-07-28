from typing import Optional, Tuple
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
        >>> # Standard workspace URL
        >>> url1 = "https://www.notion.so/demandio/c2eb1241ebbf4f39acc1ac716dae03f7"
        >>> parse_notion_url(url1)
        'c2eb1241ebbf4f39acc1ac716dae03f7'
        
        >>> # URL with title
        >>> url2 = "https://www.notion.so/demandio/My-Page-21aa14cbed00803aa901e7dd18110084"
        >>> parse_notion_url(url2)
        '21aa14cbed00803aa901e7dd18110084'
        
        >>> # URL with view parameters
        >>> url3 = "https://www.notion.so/c2eb1241ebbf4f39acc1ac716dae03f7?v=1d4a14cbed00805fbb49000cbb17b037"
        >>> parse_notion_url(url3)
        'c2eb1241ebbf4f39acc1ac716dae03f7'
    """
    if not url:
        return None
        
    # Normalize the URL
    url = url.strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        
    # UUID pattern (32 hex characters, optionally with hyphens)
    uuid_pattern = r"([a-f0-9]{8}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{12}|[a-f0-9]{32})"
    
    try:
        # First, try to find UUID in the entire URL
        match = re.search(uuid_pattern, url.lower())
        if match:
            # Clean up any hyphens and return
            return match.group(1).replace('-', '')
            
        # If no match, parse the URL
        parsed = urlparse(url)
        if not parsed.netloc.endswith('notion.so'):
            return None
            
        # Check path components
        path_parts = [p for p in parsed.path.split('/') if p]
        for part in path_parts:
            match = re.search(uuid_pattern, part.lower())
            if match:
                return match.group(1).replace('-', '')
                
        # Check query parameters
        query_params = parse_qs(parsed.query)
        for param_values in query_params.values():
            for value in param_values:
                match = re.search(uuid_pattern, value.lower())
                if match:
                    return match.group(1).replace('-', '')
                    
        return None
        
    except Exception as e:
        print(f"Error parsing Notion URL: {e}")
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

def validate_notion_id(id_str: str) -> bool:
    """
    Validate that a string is a valid Notion ID.
    
    Args:
        id_str: String to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Remove any hyphens
    clean_id = id_str.replace('-', '')
    
    # Check if it's a 32-character hex string
    return bool(re.match(r'^[a-f0-9]{32}$', clean_id.lower())) 