#!/usr/bin/env python3
"""
Script to generate user mappings by querying Slack and Notion APIs.
Creates a unified user dictionary with information from both platforms.
"""
import os
import json
from typing import Dict, Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from notion_client import Client as NotionClient
from notion_client.errors import APIResponseError
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

def get_slack_users(slack_client: WebClient) -> Dict[str, Dict]:
    """
    Fetch all users from Slack, organized by display name for matching.
    
    Returns:
        Dict mapping display names to user info
    """
    users_by_name = {}
    try:
        print("\nFetching users from Slack...")
        cursor = None
        while True:
            try:
                result = slack_client.users_list(limit=1000, cursor=cursor)
                if not result["ok"]:
                    print(f"Error in users.list: {result}")
                    break
                
                members = result.get("members", [])
                print(f"Processing {len(members)} Slack users...")
                
                for member in members:
                    # Skip bots and deleted users
                    if member.get("is_bot") or member.get("deleted"):
                        continue
                    
                    real_name = member.get("real_name", "").strip()
                    if real_name:
                        users_by_name[real_name.lower()] = {
                            "slack_id": member["id"],
                            "slack_name": f"@{member.get('name', '')}",
                            "real_name": real_name
                        }
                        print(f"Added Slack user: {real_name}")
                
                cursor = result.get("response_metadata", {}).get("next_cursor")
                if not cursor:
                    break
                    
            except SlackApiError as e:
                print(f"Error fetching users page: {e}")
                break
                
    except SlackApiError as e:
        print(f"Error fetching Slack users: {e}")
    
    print(f"\nFound {len(users_by_name)} active Slack users")
    return users_by_name

def get_notion_users(notion_client: NotionClient) -> Dict[str, Dict]:
    """
    Fetch all users from Notion with their email addresses.
    
    Returns:
        Dict mapping emails to user info
    """
    users_by_email = {}
    try:
        print("\nFetching users from Notion...")
        users = notion_client.users.list()
        
        for user in users["results"]:
            # Skip bots and users without email
            if user.get("type") == "bot" or not user.get("person", {}).get("email"):
                continue
            
            email = user["person"]["email"]
            name = user.get("name", "").strip()
            if email and name:
                users_by_email[email] = {
                    "email": email,
                    "notion_id": user["id"],
                    "notion_name": name,
                    "slack_id": None,  # Will be filled in later
                    "slack_name": None  # Will be filled in later
                }
                print(f"Added Notion user: {name} ({email})")
    
    except APIResponseError as e:
        print(f"Error fetching Notion users: {e}")
    
    print(f"\nFound {len(users_by_email)} Notion users with email addresses")
    return users_by_email

def merge_user_info(notion_users: Dict[str, Dict], slack_users: Dict[str, Dict]) -> Dict[str, Dict]:
    """
    Create unified user profiles by matching Notion and Slack users by name.
    
    Args:
        notion_users: Dict of Notion users by email
        slack_users: Dict of Slack users by display name
        
    Returns:
        Dict of unified user profiles with both Notion and Slack information
    """
    print("\nMatching users between Notion and Slack...")
    unified_users = {}
    
    for email, notion_info in notion_users.items():
        notion_name = notion_info["notion_name"].lower()
        
        # Try to find matching Slack user by name
        slack_info = slack_users.get(notion_name)
        if slack_info:
            unified_users[email] = {
                "email": email,
                "notion_id": notion_info["notion_id"],
                "notion_name": notion_info["notion_name"],
                "slack_id": slack_info["slack_id"],
                "slack_name": slack_info["slack_name"]
            }
            print(f"Matched user: {notion_info['notion_name']} ({email}) - {slack_info['slack_name']}")
        else:
            print(f"No Slack match found for Notion user: {notion_info['notion_name']} ({email})")
            unified_users[email] = notion_info  # Keep Notion info even without Slack match
    
    return unified_users

def generate_config_code(user_mappings: Dict[str, Dict]) -> str:
    """Generate Python code for the USER_MAPPINGS configuration."""
    lines = ["# User mappings with Notion and Slack information"]
    lines.append("USER_MAPPINGS: Dict[str, UserMapping] = {")
    
    for email, info in user_mappings.items():
        lines.append(f"    # {info['notion_name']}")
        lines.append(f"    \"{email}\": {{")
        lines.append(f"        \"email\": \"{info['email']}\",")
        lines.append(f"        \"notion_id\": \"{info['notion_id']}\",")
        lines.append(f"        \"notion_name\": \"{info['notion_name']}\",")
        if info.get("slack_id"):
            lines.append(f"        \"slack_id\": \"{info['slack_id']}\",")
            lines.append(f"        \"slack_name\": \"{info['slack_name']}\",")
        else:
            lines.append("        \"slack_id\": None,")
            lines.append("        \"slack_name\": None,")
        lines.append("    },")
    
    lines.append("}")
    return "\n".join(lines)

def main():
    # Get API tokens from environment
    slack_token = os.getenv("SLACK_BOT_TOKEN")
    notion_token = os.getenv("NOTION_API_KEY")
    
    if not slack_token or not notion_token:
        print("Error: Missing required environment variables.")
        print("Please ensure SLACK_BOT_TOKEN and NOTION_API_KEY are set in .env file.")
        return
    
    # Initialize clients
    slack_client = WebClient(token=slack_token)
    notion_client = NotionClient(auth=notion_token)
    
    # Get users from both platforms
    slack_users = get_slack_users(slack_client)
    notion_users = get_notion_users(notion_client)
    
    # Create unified user mappings
    unified_users = merge_user_info(notion_users, slack_users)
    print(f"\nCreated {len(unified_users)} unified user profiles")
    
    # Save raw data for reference
    with open("user_mappings_raw.json", "w") as f:
        json.dump({
            "unified_users": unified_users
        }, f, indent=2)
    print("\nSaved raw data to user_mappings_raw.json")
    
    # Generate and save configuration code
    config_code = generate_config_code(unified_users)
    with open("user_mappings_config.py", "w") as f:
        f.write(config_code)
    print("\nSaved configuration code to user_mappings_config.py")
    
    # Print summary
    print("\nUser Mapping Summary:")
    for email, info in unified_users.items():
        print(f"\nEmail: {email}")
        print(f"Notion: {info['notion_name']} ({info['notion_id']})")
        if info.get("slack_id"):
            print(f"Slack: {info['slack_name']} ({info['slack_id']})")
        else:
            print("Slack: No match found")

if __name__ == "__main__":
    main() 