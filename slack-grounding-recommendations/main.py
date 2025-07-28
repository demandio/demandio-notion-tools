import functions_framework
from typing import Dict, Any
import os

from config import MONITORING_JOBS
from utils import get_secret, parse_notion_url, construct_notion_block_url
from slack_client import SlackClient
from notion_client import NotionClient
from ai_analyzer import AIAnalyzer

def initialize_clients(project_id: str) -> tuple:
    """Initialize API clients using secrets from GCP Secret Manager."""
    notion_token = get_secret("notion-api-key", project_id)
    slack_token = get_secret("slack-bot-token", project_id)
    anthropic_key = get_secret("anthropic-api-key", project_id)
    
    return (
        NotionClient(notion_token),
        SlackClient(slack_token),
        AIAnalyzer(anthropic_key)
    )

def process_monitoring_job(
    job: Dict[str, Any],
    notion_client: NotionClient,
    slack_client: SlackClient,
    ai_analyzer: AIAnalyzer
) -> None:
    """Process a single monitoring job."""
    # Extract page ID from Notion URL
    page_id = parse_notion_url(job["notion_page_url"])
    if not page_id:
        print(f"Invalid Notion URL in job {job['job_name']}")
        return
        
    try:
        # 1. Get page owner's email
        owner_email = notion_client.get_page_owner_email(page_id)
        if not owner_email:
            print(f"Could not find owner email for page {page_id}")
            return
            
        # 2. Get owner's Slack ID
        slack_user_id = slack_client.get_user_id_by_email(owner_email)
        if not slack_user_id:
            print(f"Could not find Slack user for email {owner_email}")
            return
            
        # 3. Get Notion blocks
        notion_blocks = notion_client.get_page_blocks(page_id)
        if not notion_blocks:
            print(f"No blocks found in page {page_id}")
            return
            
        # 4. Get Slack messages
        slack_messages = slack_client.get_messages_from_channels(job["slack_channel_ids"])
        if not slack_messages:
            print(f"No messages found in channels {job['slack_channel_ids']}")
            return
            
        # 5. Generate suggestions using AI
        suggestions = ai_analyzer.generate_suggestions(notion_blocks, slack_messages)
        
        # 6. Process each suggestion
        for suggestion in suggestions:
            # Add the Notion deep link
            suggestion["notion_url"] = construct_notion_block_url(page_id, suggestion["block_id"])
            
            # Send suggestion to user
            success = slack_client.post_suggestion_to_user(slack_user_id, suggestion)
            if success:
                print(f"Successfully sent suggestion for block {suggestion['block_id']} to user {slack_user_id}")
            else:
                print(f"Failed to send suggestion for block {suggestion['block_id']} to user {slack_user_id}")
                
    except Exception as e:
        print(f"Error processing job {job['job_name']}: {e}")

@functions_framework.http
def monitor_notion_slack(request) -> tuple:
    """
    Cloud Function entry point.
    
    This function is triggered by Cloud Scheduler and processes all monitoring jobs.
    """
    try:
        # Get GCP project ID from environment
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            return "Missing GOOGLE_CLOUD_PROJECT environment variable", 500
            
        # Initialize clients
        notion_client, slack_client, ai_analyzer = initialize_clients(project_id)
        
        # Process each monitoring job
        for job in MONITORING_JOBS:
            process_monitoring_job(job, notion_client, slack_client, ai_analyzer)
            
        return "Successfully processed all monitoring jobs", 200
        
    except Exception as e:
        print(f"Error in monitor_notion_slack: {e}")
        return f"Error: {str(e)}", 500

if __name__ == "__main__":
    # For local testing
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if project_id:
        notion_client, slack_client, ai_analyzer = initialize_clients(project_id)
        for job in MONITORING_JOBS:
            process_monitoring_job(job, notion_client, slack_client, ai_analyzer) 