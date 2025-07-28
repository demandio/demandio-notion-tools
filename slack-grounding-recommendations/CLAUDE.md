# Slack Grounding Recommendations Tool

This tool monitors Notion documents and Slack channels for potential conflicts or updates needed, using Claude AI to analyze conversations and suggest document updates.

## Architecture

```
slack-grounding-recommendations/
├── main.py                 # Cloud Function entry point
├── config.py              # Configuration and user mappings
├── utils.py              # Shared utilities
├── slack_client.py       # Slack API interactions
├── notion_client.py      # Notion API interactions
├── ai_analyzer.py        # Claude AI integration
└── scripts/             # Utility scripts
    └── generate_user_mappings.py  # User profile generator
```

## Key Concepts

### Monitoring Jobs
- Defined in `config.py` as `MONITORING_JOBS`
- Each job pairs Notion documents with Slack channels
- Includes document owner information for notifications
- Example structure:
```python
{
    "job_name": "Project Grounding",
    "notion_page_url": "https://notion.so/...",
    "notion_page_id": "page_id",
    "slack_channel_ids": ["channel1", "channel2"],
    "owner_email": "owner@demand.io"
}
```

### User Mappings
- Stored in `config.py` as `USER_MAPPINGS`
- Maps user information across Notion and Slack
- Used for notifications and mentions
- Structure:
```python
{
    "user@demand.io": {
        "email": "user@demand.io",
        "notion_id": "notion-user-id",
        "notion_name": "User Name",
        "slack_id": "U0XXXXXXXX",
        "slack_name": "@username"
    }
}
```

## Important Workflows

### Message Analysis
1. Fetch messages from configured Slack channels
2. Include all thread replies and responses
3. Group messages by thread for context
4. Compare against Notion content
5. Generate suggestions with deep links

### Notification Flow
1. Identify document conflicts
2. Find document owner in user mappings
3. Format suggestion with context
4. Send Slack notification with deep links
5. Include thread context if relevant

## Configuration Guidelines

### Adding New Monitoring Pairs
1. Use `create_monitoring_job` helper in `config.py`
2. Provide Notion URL and Slack channel IDs
3. Include owner's email for notifications
4. Example:
```python
create_monitoring_job(
    name="New Monitor",
    url="https://notion.so/page",
    channel_ids=["C0XXXXXX"],
    owner_email="owner@demand.io"
)
```

### Updating User Mappings
1. Run `scripts/generate_user_mappings.py`
2. Review generated mappings in `user_mappings_raw.json`
3. Copy relevant entries to `config.py`
4. Update as team members change

## Development Guidelines

### AI Prompt Engineering
- Include thread context in prompts
- Focus on factual conflicts
- Consider consensus in threads
- Provide specific block references
- Include confidence scores

### API Best Practices
- Handle Slack pagination properly
- Fetch complete thread context
- Use proper Notion block operations
- Implement rate limiting
- Cache responses when possible

### Error Handling
- Handle missing user mappings gracefully
- Validate Notion URLs and IDs
- Check Slack channel access
- Log API errors with context
- Implement retries for transient failures

## Testing

### Unit Tests
- Test URL parsing in `utils.py`
- Validate user mapping functions
- Check monitoring job creation
- Verify AI prompt construction

### Integration Tests
- Test Slack message fetching
- Verify Notion block access
- Check notification delivery
- Validate thread handling

## Deployment

### Prerequisites
1. Enable Cloud Functions API
2. Configure Secret Manager
3. Set up service account
4. Grant necessary permissions

### Environment Variables
Required in GCP Secret Manager:
- `NOTION_API_KEY`
- `SLACK_BOT_TOKEN`
- `ANTHROPIC_API_KEY`
- `GOOGLE_CLOUD_PROJECT`

### Cloud Function Settings
- Runtime: Python 3.9+
- Memory: 512MB minimum
- Timeout: 120 seconds
- Schedule: Every 5 minutes

## Troubleshooting

### Common Issues
1. Missing Slack permissions
   - Check bot token scopes
   - Verify channel access
2. Notion rate limits
   - Implement backoff
   - Cache responses
3. User mapping mismatches
   - Update mappings
   - Check email formats

### Debugging
- Enable detailed logging
- Check Cloud Function logs
- Monitor API quotas
- Verify user permissions 