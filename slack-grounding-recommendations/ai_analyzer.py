from typing import List, Dict
import anthropic
from datetime import datetime

class AIAnalyzer:
    def __init__(self, api_key: str):
        """
        Initialize the Claude AI client.
        
        Args:
            api_key: Anthropic API key
        """
        self.client = anthropic.Client(api_key=api_key)
        
    def generate_suggestions(self, notion_blocks: List[Dict], slack_messages: List[Dict]) -> List[Dict]:
        """
        Generate suggestions for document updates based on Slack messages.
        
        Args:
            notion_blocks: List of Notion blocks with their content
            slack_messages: List of Slack messages to analyze
            
        Returns:
            List of suggestions with block IDs and proposed changes
        """
        # Format blocks and messages for the prompt
        formatted_blocks = self._format_blocks(notion_blocks)
        formatted_messages = self._format_messages(slack_messages)
        
        # Construct the prompt
        prompt = self._construct_prompt(formatted_blocks, formatted_messages)
        
        try:
            # Call Claude API
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4000,
                temperature=0.0,  # Use deterministic output
                system="You are an expert Technical Program Manager analyzing Slack messages for potential updates to Notion documentation.",
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse the structured response
            suggestions = self._parse_suggestions(response.content)
            return suggestions
            
        except Exception as e:
            print(f"Error generating suggestions: {e}")
            return []
            
    def _format_blocks(self, blocks: List[Dict]) -> str:
        """Format Notion blocks for the prompt."""
        formatted = []
        for block in blocks:
            formatted.append(
                f"BLOCK_ID: {block['id']}\n"
                f"TYPE: {block['type']}\n"
                f"CONTENT: {block['content']}\n"
            )
        return "\n---\n".join(formatted)
        
    def _format_messages(self, messages: List[Dict]) -> str:
        """Format Slack messages for the prompt, preserving thread context."""
        formatted = []
        
        # Group messages by thread
        threads: Dict[str, List[Dict]] = {}
        standalone_messages: List[Dict] = []
        
        for msg in messages:
            if msg.get("is_thread_reply"):
                parent_ts = msg.get("parent_ts")
                if parent_ts not in threads:
                    threads[parent_ts] = []
                threads[parent_ts].append(msg)
            elif msg.get("thread_ts"):
                # This is a parent message with replies
                if msg["ts"] not in threads:
                    threads[msg["ts"]] = []
                threads[msg["ts"]].insert(0, msg)  # Put parent first
            else:
                # Standalone message
                standalone_messages.append(msg)
        
        # Format threaded conversations
        for thread_messages in threads.values():
            parent = thread_messages[0]  # Parent message is first
            thread_text = [
                f"THREAD START - {datetime.fromtimestamp(float(parent['ts'])).isoformat()}\n"
                f"LINK: {parent.get('permalink', 'N/A')}\n"
                f"PARENT MESSAGE: {parent.get('text', '')}\n"
            ]
            
            # Add replies in chronological order
            for reply in thread_messages[1:]:
                thread_text.append(
                    f"REPLY - {datetime.fromtimestamp(float(reply['ts'])).isoformat()}\n"
                    f"LINK: {reply.get('permalink', 'N/A')}\n"
                    f"TEXT: {reply.get('text', '')}\n"
                )
            
            thread_text.append("THREAD END\n")
            formatted.append("\n".join(thread_text))
        
        # Format standalone messages
        for msg in standalone_messages:
            formatted.append(
                f"MESSAGE - {datetime.fromtimestamp(float(msg['ts'])).isoformat()}\n"
                f"LINK: {msg.get('permalink', 'N/A')}\n"
                f"TEXT: {msg.get('text', '')}\n"
            )
        
        return "\n---\n".join(formatted)

    def _construct_prompt(self, formatted_blocks: str, formatted_messages: str) -> str:
        """Construct the prompt for Claude."""
        return f"""
        **ROLE AND GOAL:**
        You are an expert Technical Program Manager analyzing Slack messages and their thread replies to identify potential updates needed in Notion documentation. Your goal is to identify conflicts, new information, or outdated content.

        **PRIMARY CONTEXT: The Source of Truth (Notion Blocks)**
        {formatted_blocks}

        **INPUT DATA: Recent Slack Messages and Threads**
        {formatted_messages}

        **YOUR TASK:**
        Carefully analyze each Slack message and its thread replies, comparing them against the Notion blocks. Pay special attention to threaded conversations as they often contain important clarifications, corrections, or updates. Identify messages that contain:
        1. New information not present in the documentation
        2. Updates to existing information
        3. Direct conflicts with documented information
        4. Important clarifications or corrections found in thread replies
        5. Consensus or final decisions reached in thread discussions

        **RULES:**
        1. Focus on factual conflicts or definitive updates only
        2. Each suggestion must reference a specific BLOCK_ID
        3. Consider the full context of threaded conversations
        4. Pay special attention to thread conclusions and consensus
        5. Provide high confidence suggestions only
        6. Consider context and avoid superficial changes

        **REQUIRED OUTPUT FORMAT:**
        For each suggestion, provide:

        **Suggestion N**
        * **Source Message Link:** `<Link to the Slack message>`
        * **Thread Context:** `<Brief summary of relevant thread discussion if applicable>`
        * **Triggering Text:** "`<Quote the exact phrase from Slack.>`"
        * **Conflicting Block ID:** "`<The exact BLOCK_ID of the outdated Notion block.>`"
        * **Conflicting Text in Block:** "`<Quote the specific sentence from the Notion block's content.>`"
        * **Suggested Edit:** "`<Write the new, updated text for the block.>`"
        * **Reasoning:** `<Explain why this is a necessary update in one sentence.>`
        * **Confidence Score:** `<High/Medium/Low>`

        If no valid suggestions are found, respond with "No suggestions found."
        """
        
    def _parse_suggestions(self, response: str) -> List[Dict]:
        """
        Parse Claude's response into structured suggestions.
        
        This is a basic implementation that should be enhanced with more robust parsing.
        """
        suggestions = []
        
        if "No suggestions found." in response:
            return suggestions
            
        # Split response into individual suggestions
        parts = response.split("**Suggestion")
        
        for part in parts[1:]:  # Skip the first split as it's empty
            try:
                # Extract fields using string manipulation
                # This is a basic implementation - consider using regex for more robust parsing
                suggestion = {}
                
                # Extract link
                link_start = part.find("**Source Message Link:**") + len("**Source Message Link:**")
                link_end = part.find("**Thread Context:**")
                suggestion["source_message_link"] = part[link_start:link_end].strip().strip("`")
                
                # Extract thread context
                context_start = part.find("**Thread Context:**") + len("**Thread Context:**")
                context_end = part.find("**Triggering Text:**")
                suggestion["thread_context"] = part[context_start:context_end].strip().strip('"')
                
                # Extract triggering text
                text_start = part.find("**Triggering Text:**") + len("**Triggering Text:**")
                text_end = part.find("**Conflicting Block ID:**")
                suggestion["triggering_text"] = part[text_start:text_end].strip().strip('"')
                
                # Extract block ID
                block_start = part.find("**Conflicting Block ID:**") + len("**Conflicting Block ID:**")
                block_end = part.find("**Conflicting Text in Block:**")
                suggestion["block_id"] = part[block_start:block_end].strip().strip('"')
                
                # Extract conflicting text
                conflict_start = part.find("**Conflicting Text in Block:**") + len("**Conflicting Text in Block:**")
                conflict_end = part.find("**Suggested Edit:**")
                suggestion["conflicting_text"] = part[conflict_start:conflict_end].strip().strip('"')
                
                # Extract suggested edit
                edit_start = part.find("**Suggested Edit:**") + len("**Suggested Edit:**")
                edit_end = part.find("**Reasoning:**")
                suggestion["suggested_edit"] = part[edit_start:edit_end].strip().strip('"')
                
                # Extract reasoning
                reason_start = part.find("**Reasoning:**") + len("**Reasoning:**")
                reason_end = part.find("**Confidence Score:**")
                suggestion["reasoning"] = part[reason_start:reason_end].strip().strip("`")
                
                # Extract confidence
                conf_start = part.find("**Confidence Score:**") + len("**Confidence Score:**")
                suggestion["confidence_score"] = part[conf_start:].strip().strip("`")
                
                suggestions.append(suggestion)
                
            except Exception as e:
                print(f"Error parsing suggestion: {e}")
                continue
                
        return suggestions 