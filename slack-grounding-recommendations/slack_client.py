from datetime import datetime, timedelta
from typing import List, Dict, Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from config import get_user_by_email, get_user_by_slack_id, UserMapping

class SlackClient:
    def __init__(self, token: str):
        """
        Initialize the Slack client.
        
        Args:
            token: Slack bot token
        """
        self.client = WebClient(token=token)
        
    def get_messages_from_channels(self, channel_ids: List[str], days: int = 7) -> List[Dict]:
        """
        Fetch messages and their thread replies from specified channels within the last N days.
        
        Args:
            channel_ids: List of Slack channel IDs
            days: Number of days to look back (default: 7)
            
        Returns:
            List of messages with their metadata and thread replies
        """
        messages = []
        oldest = (datetime.now() - timedelta(days=days)).timestamp()
        
        for channel_id in channel_ids:
            try:
                # Fetch messages using conversations.history
                result = self.client.conversations_history(
                    channel=channel_id,
                    oldest=oldest,
                    limit=1000,  # Adjust as needed
                    include_all_metadata=True  # Get additional message metadata
                )
                
                if result["ok"]:
                    # Process each message
                    for msg in result["messages"]:
                        # Add channel context
                        msg["channel_id"] = channel_id
                        
                        # Get message permalink
                        try:
                            permalink_result = self.client.chat_getPermalink(
                                channel=channel_id,
                                message_ts=msg["ts"]
                            )
                            if permalink_result["ok"]:
                                msg["permalink"] = permalink_result["permalink"]
                        except SlackApiError as e:
                            print(f"Error getting permalink for message {msg['ts']}: {e}")
                            msg["permalink"] = f"https://slack.com/archives/{channel_id}/p{msg['ts'].replace('.', '')}"
                        
                        # Add the main message
                        messages.append(msg)
                        
                        # If message has thread replies, fetch them
                        if msg.get("thread_ts") or msg.get("reply_count", 0) > 0:
                            try:
                                thread_result = self.client.conversations_replies(
                                    channel=channel_id,
                                    ts=msg["ts" if not msg.get("thread_ts") else "thread_ts"],
                                    limit=1000  # Adjust as needed
                                )
                                
                                if thread_result["ok"]:
                                    for reply in thread_result["messages"]:
                                        # Skip the parent message as we already have it
                                        if reply["ts"] == msg["ts"]:
                                            continue
                                            
                                        # Add thread context
                                        reply["channel_id"] = channel_id
                                        reply["is_thread_reply"] = True
                                        reply["parent_ts"] = msg["ts"]
                                        
                                        # Get reply permalink
                                        try:
                                            reply_permalink = self.client.chat_getPermalink(
                                                channel=channel_id,
                                                message_ts=reply["ts"]
                                            )
                                            if reply_permalink["ok"]:
                                                reply["permalink"] = reply_permalink["permalink"]
                                        except SlackApiError as e:
                                            print(f"Error getting permalink for reply {reply['ts']}: {e}")
                                            reply["permalink"] = f"https://slack.com/archives/{channel_id}/p{reply['ts'].replace('.', '')}"
                                        
                                        messages.append(reply)
                                        
                            except SlackApiError as e:
                                print(f"Error fetching thread replies for message {msg['ts']}: {e}")
                        
            except SlackApiError as e:
                print(f"Error fetching messages from channel {channel_id}: {e}")
                
        return messages
        
    def get_user_id_by_email(self, email: str) -> Optional[str]:
        """
        Look up a Slack user ID by their email address.
        First checks the USER_MAPPINGS, then falls back to Slack API.
        
        Args:
            email: User's email address
            
        Returns:
            Slack user ID if found, None otherwise
        """
        # First check our user mappings
        user = get_user_by_email(email)
        if user:
            return user["slack_id"]
            
        # Fall back to Slack API
        try:
            result = self.client.users_lookupByEmail(email=email)
            if result["ok"]:
                return result["user"]["id"]
        except SlackApiError as e:
            print(f"Error looking up user by email {email}: {e}")
        return None
        
    def post_suggestion_to_user(self, user_id: str, suggestion: Dict) -> bool:
        """
        Post a suggestion message to a user using Block Kit formatting.
        
        Args:
            user_id: Slack user ID to send message to
            suggestion: Dictionary containing suggestion details
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        try:
            # Get user info for personalization
            user = get_user_by_slack_id(user_id)
            greeting = f"Hi {user['slack_name'] if user else 'there'}"
            
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🔄 Potential Document Update Needed"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{greeting}! I found a potential update needed in your Notion document."
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Source:* {suggestion['source_message_link']}\n"
                               f"*Triggering Text:* {suggestion['triggering_text']}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Current Text:* {suggestion['conflicting_text']}\n"
                               f"*Suggested Update:* {suggestion['suggested_edit']}"
                    }
                }
            ]
            
            # Add thread context if available
            if suggestion.get("thread_context"):
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Thread Context:* {suggestion['thread_context']}"
                    }
                })
            
            blocks.extend([
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Reasoning:* {suggestion['reasoning']}\n"
                               f"*Confidence:* {suggestion['confidence_score']}"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "View in Notion"
                            },
                            "url": suggestion["notion_url"],
                            "style": "primary"
                        }
                    ]
                }
            ])
            
            result = self.client.chat_postMessage(
                channel=user_id,
                blocks=blocks,
                text=f"{greeting}! I found a potential update needed in your Notion document."  # Fallback text
            )
            return result["ok"]
            
        except SlackApiError as e:
            print(f"Error posting suggestion to user {user_id}: {e}")
            return False 