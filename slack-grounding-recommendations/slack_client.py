from datetime import datetime, timedelta
from typing import List, Dict, Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

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
        Fetch messages from specified channels within the last N days.
        
        Args:
            channel_ids: List of Slack channel IDs
            days: Number of days to look back (default: 7)
            
        Returns:
            List of messages with their metadata
        """
        messages = []
        oldest = (datetime.now() - timedelta(days=days)).timestamp()
        
        for channel_id in channel_ids:
            try:
                # Fetch messages using conversations.history
                result = self.client.conversations_history(
                    channel=channel_id,
                    oldest=oldest,
                    limit=1000  # Adjust as needed
                )
                
                if result["ok"]:
                    # Add channel context to each message
                    for msg in result["messages"]:
                        msg["channel_id"] = channel_id
                        messages.append(msg)
                        
            except SlackApiError as e:
                print(f"Error fetching messages from channel {channel_id}: {e}")
                
        return messages
        
    def get_user_id_by_email(self, email: str) -> Optional[str]:
        """
        Look up a Slack user ID by their email address.
        
        Args:
            email: User's email address
            
        Returns:
            Slack user ID if found, None otherwise
        """
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
                },
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
            ]
            
            result = self.client.chat_postMessage(
                channel=user_id,
                blocks=blocks,
                text="A potential document update has been identified."  # Fallback text
            )
            return result["ok"]
            
        except SlackApiError as e:
            print(f"Error posting suggestion to user {user_id}: {e}")
            return False 