import os
from typing import List, Dict, TypedDict
from shared.env import (
    load_tool_env,
    get_notion_api_key,
    get_slack_bot_token,
    get_anthropic_api_key
)

# Load tool-specific environment variables
load_tool_env('slack-grounding-recommendations')

class MonitoringJob(TypedDict):
    job_name: str
    notion_page_url: str
    slack_channel_ids: List[str]

# Central configuration for monitoring jobs
MONITORING_JOBS: List[MonitoringJob] = [
    {
        "job_name": "ShopGraph Grounding Monitor",
        "notion_page_url": "https://www.notion.so/demandio/c2eb1241ebbf4f39acc1ac716dae03f7?v=1d4a14cbed00805fbb49000cbb17b037&p=206a14cbed0080a2abc3e1a3a51d8450&pm=s",
        "slack_channel_ids": ["C07CWGEL6Q6", "C07ABCD1234"]
    }
]

# Environment variables
NOTION_API_KEY = get_notion_api_key()
SLACK_BOT_TOKEN = get_slack_bot_token()
ANTHROPIC_API_KEY = get_anthropic_api_key()

# Validation
if not all([NOTION_API_KEY, SLACK_BOT_TOKEN, ANTHROPIC_API_KEY]):
    raise ValueError("Missing required environment variables. Please check your .env file.") 