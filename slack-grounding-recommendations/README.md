# Notion-Slack Grounding Tool

A serverless Python application that monitors Slack conversations and suggests updates to Notion documentation when it detects potential conflicts or outdated information.

## Features

- 🔄 Weekly automated monitoring of Slack channels and Notion pages
- 🤖 AI-powered analysis using Claude to identify conflicts and suggest updates
- 🔗 Direct deep-links to specific Notion blocks that need updating
- 📧 Automatic notification of document owners via Slack
- ⚙️ Configurable monitoring jobs for multiple document-channel pairs

## Architecture

The application runs on Google Cloud Platform using:

- **Google Cloud Functions**: Serverless execution environment
- **Google Cloud Scheduler**: Triggers weekly monitoring jobs
- **Google Secret Manager**: Secure storage of API keys
- **Notion API**: Access to document content and metadata
- **Slack API**: Message history and user notifications
- **Claude API**: AI-powered content analysis

## Setup

1. **Create Required Secrets in GCP Secret Manager**:
   ```bash
   # Create secrets
   gcloud secrets create notion-api-key --data-file=/path/to/notion-key.txt
   gcloud secrets create slack-bot-token --data-file=/path/to/slack-token.txt
   gcloud secrets create anthropic-api-key --data-file=/path/to/anthropic-key.txt
   ```

2. **Configure Monitoring Jobs**:
   Edit `config.py` to add your Notion-Slack pairs:
   ```python
   MONITORING_JOBS = [
       {
           "job_name": "Project Documentation Monitor",
           "notion_page_url": "https://notion.so/your-page-url",
           "slack_channel_ids": ["CHANNEL_ID1", "CHANNEL_ID2"]
       }
   ]
   ```

3. **Deploy to Google Cloud Functions**:
   ```bash
   # Deploy the function
   gcloud functions deploy notion-slack-monitor \
       --runtime python311 \
       --trigger-http \
       --entry-point monitor_notion_slack \
       --memory 512MB \
       --timeout 540s
   ```

4. **Set Up Cloud Scheduler**:
   ```bash
   # Create a weekly trigger
   gcloud scheduler jobs create http notion-slack-weekly \
       --schedule "0 0 * * 1" \
       --uri "YOUR_FUNCTION_URL" \
       --http-method POST
   ```

## Local Development

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**:
   Create a `.env` file:
   ```
   GOOGLE_CLOUD_PROJECT=your-project-id
   NOTION_API_KEY=your-notion-key
   SLACK_BOT_TOKEN=your-slack-token
   ANTHROPIC_API_KEY=your-anthropic-key
   ```

3. **Run Locally**:
   ```bash
   python main.py
   ```

## Required Permissions

### Notion
- Read access to pages and blocks
- Access to page properties (for owner information)

### Slack
- `channels:history`: Read message history
- `users:read.email`: Look up users by email
- `chat:write`: Send messages to users

### Google Cloud
- `secretmanager.secrets.get`: Access secrets
- `cloudfunctions.functions.invoke`: Execute functions
- `cloudscheduler.jobs.create`: Create scheduler jobs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details 