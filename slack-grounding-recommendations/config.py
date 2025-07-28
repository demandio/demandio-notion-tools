import os
from typing import List, Dict, TypedDict, Optional
from shared.env import (
    load_tool_env,
    get_notion_api_key,
    get_slack_bot_token,
    get_anthropic_api_key
)
from utils import parse_notion_url

# Load tool-specific environment variables
load_tool_env('slack-grounding-recommendations')

class MonitoringJob(TypedDict):
    job_name: str
    notion_page_url: str
    notion_page_id: str
    slack_channel_ids: List[str]
    owner_email: str  # Added to specify document owner

class UserMapping(TypedDict):
    email: str
    slack_id: str
    slack_name: str
    notion_name: str

# User mappings for document owners and relevant team members
USER_MAPPINGS: Dict[str, UserMapping] = {
    # Example format:
    # "user.name@demandio.com": {
    #     "email": "user.name@demandio.com",
    #     "slack_id": "U0XXXXXXXX",
    #     "slack_name": "@username",
    #     "notion_name": "User Name"
    # }
    "cansu@demandio.com": {
        "email": "cansu@demandio.com",
        "slack_id": "U05QXQXQXQX",  # Replace with actual Slack ID
        "slack_name": "@cansu",
        "notion_name": "Cansu Kaya"
    }
    # Add more users as needed
}

def get_user_by_email(email: str) -> Optional[UserMapping]:
    """Get user information by email."""
    return USER_MAPPINGS.get(email)

def get_user_by_slack_id(slack_id: str) -> Optional[UserMapping]:
    """Get user information by Slack ID."""
    return next(
        (user for user in USER_MAPPINGS.values() if user["slack_id"] == slack_id),
        None
    )

def get_user_by_notion_name(notion_name: str) -> Optional[UserMapping]:
    """Get user information by Notion display name."""
    return next(
        (user for user in USER_MAPPINGS.values() if user["notion_name"] == notion_name),
        None
    )

# Helper function to create a monitoring job with extracted page ID
def create_monitoring_job(name: str, url: str, channel_ids: List[str], owner_email: str) -> MonitoringJob:
    """
    Create a monitoring job with page ID extraction.
    
    Args:
        name: Job name
        url: Notion page URL
        channel_ids: List of Slack channel IDs to monitor
        owner_email: Email of the document owner
        
    Returns:
        MonitoringJob configuration
        
    Raises:
        ValueError: If page ID cannot be extracted or owner email is invalid
    """
    page_id = parse_notion_url(url)
    if not page_id:
        raise ValueError(f"Could not extract page ID from URL: {url}")
        
    if owner_email not in USER_MAPPINGS:
        raise ValueError(f"Owner email {owner_email} not found in USER_MAPPINGS")
        
    return {
        "job_name": name,
        "notion_page_url": url,
        "notion_page_id": page_id,
        "slack_channel_ids": channel_ids,
        "owner_email": owner_email
    }

# Central configuration for monitoring jobs
MONITORING_JOBS: List[MonitoringJob] = [
    # Example 1: Single Notion page monitored against multiple Slack channels
    create_monitoring_job(
        name="ShopGraph Grounding Monitor",
        url="https://www.notion.so/demandio/c2eb1241ebbf4f39acc1ac716dae03f7?v=1d4a14cbed00805fbb49000cbb17b037&p=206a14cbed0080a2abc3e1a3a51d8450&pm=s",
        channel_ids=["C07CWGEL6Q6", "C07ABCD1234"],
        owner_email="cansu@demandio.com"  # Replace with actual owner email
    ),
    
    create_monitoring_job(
        name="SEO MLP Grounding Monitor",
        url="https://www.notion.so/demandio/P2-SIMPLYCODES-complete-SEO-MLP-grounding-21aa14cbed00803aa901e7dd18110084",
        channel_ids=["C017KDKRZN1", "C086S9V4LS1"],
        owner_email="cansu@demandio.com"  # Replace with actual owner email
    )
]

# Environment variables
NOTION_API_KEY = get_notion_api_key()
SLACK_BOT_TOKEN = get_slack_bot_token()
ANTHROPIC_API_KEY = get_anthropic_api_key()

# Validation
if not all([NOTION_API_KEY, SLACK_BOT_TOKEN, ANTHROPIC_API_KEY]):
    raise ValueError("Missing required environment variables. Please check your .env file.")

# Print monitoring configuration for easy reference
print("\nMonitoring Configuration:")
for job in MONITORING_JOBS:
    owner = USER_MAPPINGS[job['owner_email']]
    print(f"\n{job['job_name']}:")
    print(f"  Page ID: {job['notion_page_id']}")
    print(f"  Owner: {owner['notion_name']} ({owner['slack_name']})")
    print(f"  Channels: {', '.join(job['slack_channel_ids'])}") 