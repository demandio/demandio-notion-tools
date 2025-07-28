"""
Shared environment variable handling for all DemandIO Notion tools.
"""
import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# First, try to load from root .env
root_env = Path(__file__).parent.parent / '.env'
if root_env.exists():
    load_dotenv(root_env)

# Then load tool-specific .env if it exists (this will override root values)
def load_tool_env(tool_name: str) -> None:
    """
    Load tool-specific environment variables.
    These will override any root-level variables.
    
    Args:
        tool_name: Name of the tool directory (e.g., 'notion-drive-sync')
    """
    tool_env = Path(__file__).parent.parent / tool_name / '.env'
    if tool_env.exists():
        load_dotenv(tool_env, override=True)

def get_required_env(key: str) -> str:
    """
    Get a required environment variable.
    
    Args:
        key: Environment variable name
        
    Returns:
        The environment variable value
        
    Raises:
        ValueError: If the environment variable is not set
    """
    value = os.getenv(key)
    if value is None:
        raise ValueError(f"Required environment variable {key} is not set")
    return value

def get_optional_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get an optional environment variable.
    
    Args:
        key: Environment variable name
        default: Default value if not set
        
    Returns:
        The environment variable value or default
    """
    return os.getenv(key, default)

# Shared environment variables
def get_notion_api_key() -> str:
    """Get the Notion API key."""
    return get_required_env("NOTION_API_KEY")

def get_gcp_project_id() -> str:
    """Get the Google Cloud project ID."""
    return get_required_env("GOOGLE_CLOUD_PROJECT")

def get_anthropic_api_key() -> str:
    """Get the Anthropic API key."""
    return get_required_env("ANTHROPIC_API_KEY")

def get_openai_api_key() -> str:
    """Get the OpenAI API key."""
    return get_required_env("OPENAI_API_KEY")

def get_gemini_api_key() -> str:
    """Get the Google Gemini API key."""
    return get_required_env("GEMINI_API_KEY")

def get_slack_bot_token() -> str:
    """Get the Slack bot token."""
    token = get_required_env("SLACK_BOT_TOKEN")
    if not token.startswith("xoxb-"):
        raise ValueError("Invalid Slack bot token format. Must start with 'xoxb-'")
    return token

# Tool-specific environment variables
def get_drive_folder_id() -> str:
    """Get the Google Drive folder ID for notion-drive-sync."""
    return get_required_env("GOOGLE_DRIVE_FOLDER_ID") 