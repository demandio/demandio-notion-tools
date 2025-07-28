# Demandio Notion Tools

This repository contains tools for integrating Notion with various services. Below are the key conventions and guidelines for working with this codebase.

## Project Structure

```
demandio-notion-tools/
├── notion-drive-sync/       # Syncs Notion documents to Google Drive
├── slack-grounding-recommendations/  # Monitors Notion-Slack pairs for conflicts
└── shared/                  # Shared utilities and configurations
```

## Environment Variables

This project uses a two-level approach to environment variables:

1. **Root Level** (`.env` in repository root):
   - `NOTION_API_KEY` - Shared Notion API key
   - `GOOGLE_CLOUD_PROJECT` - GCP project ID
   - `ANTHROPIC_API_KEY` - Claude API key
   - `OPENAI_API_KEY` - OpenAI API key
   - `GEMINI_API_KEY` - Google Gemini API key

2. **Tool Level** (`.env` in tool directories):
   - Tool-specific variables defined in each tool's directory
   - Example: `GOOGLE_DRIVE_FOLDER_ID` for notion-drive-sync

## Development Conventions

### Python Standards
- Python 3.9+ required
- Use virtual environments (`venv`) for each tool
- Format code with Black
- Type hints required for function parameters and returns
- Docstrings required for modules, classes, and functions

### Error Handling
- Use descriptive error messages
- Log errors with appropriate context
- Handle API rate limits and retries gracefully

### API Interactions
- Use official SDKs when available
- Implement pagination for list operations
- Handle rate limits with exponential backoff
- Cache API responses when appropriate

### Testing
- Unit tests required for utility functions
- Integration tests for API interactions
- Mock external API calls in tests

### Documentation
- README.md in each tool directory
- Type hints and docstrings for all public functions
- Examples for complex operations
- Update docs when adding new features

## Common Operations

### Setting Up a New Tool
1. Create a new directory
2. Add requirements.txt
3. Create tool-specific .env
4. Update shared environment variables if needed

### Deploying to GCP
1. Enable required APIs in GCP console
2. Set up service account with minimal permissions
3. Deploy using gcloud CLI
4. Configure Cloud Scheduler for periodic execution

## Tool-Specific Guidelines

Each tool has its own CLAUDE.md file with specific instructions:
- [notion-drive-sync/CLAUDE.md](./notion-drive-sync/CLAUDE.md)
- [slack-grounding-recommendations/CLAUDE.md](./slack-grounding-recommendations/CLAUDE.md)

## Best Practices

### Security
- Never commit .env files
- Use Secret Manager for production secrets
- Rotate API keys regularly
- Audit API permissions regularly

### Performance
- Implement caching where appropriate
- Use batch operations when possible
- Monitor API usage and quotas
- Log execution times for optimization

### Maintenance
- Keep dependencies updated
- Monitor API deprecation notices
- Regular security audits
- Backup important configurations 