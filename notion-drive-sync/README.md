# Notion to Google Drive Sync

  Overview

  This script is a Google Cloud Function that syncs Notion pages to Google
  Drive in two formats:
  1. Plain text files (.txt) - saved to folder 0ADh8oHDMGlVNUk9PVA
  2. Google Docs (.gdoc) - saved to folder 0AE4_IKRqRvtYUk9PVA

  How It Works

  Webhook Flow

  1. Notion button triggers webhook to https://us-central1-demand-io-base.cloudfunctions.net/sync_notion_to_drive
  2. Service Account: 640633174857-compute@developer.gserviceaccount.com
  3. Function receives webhook payload and extracts page ID
  4. Syncs the page as both .txt and .gdoc formats
  5. Returns success/error response

## ✨ Features

### 🔄 **Automatic Sync**
- Webhook-triggered sync from Notion pages
- Background processing prevents timeout errors
- Immediate success response to Notion

### 📄 **Dual Format Output** 
- **Plain Text (.txt)**: Clean, readable text format
- **Google Docs**: Rich HTML format with proper styling

### 🏷️ **Comprehensive Metadata Extraction**
- **All Notion Properties**: Automatically extracts and includes all non-empty page properties
- **Smart Type Handling**: Supports all Notion property types:
  - Text, Numbers, Dates, URLs, Email, Phone
  - Single/Multi-select, Status, Checkboxes
  - People, Files, Relations, Formulas, Rollups
  - Created/edited timestamps and users
- **Clean Formatting**: Property names formatted nicely (snake_case → Title Case)

### 🎯 **Organized Storage**
- Separate Google Drive folders for TXT and Google Docs
- Sanitized filenames for compatibility
- Rich metadata headers in all documents

### 🔒 **Enterprise Ready**
- Google Cloud authentication
- Webhook signature verification
- Comprehensive logging
- Error handling with graceful fallbacks

## 🚀 Quick Start

### Prerequisites

- Google Cloud Project with billing enabled
- Notion integration with API access
- Google Drive API enabled
- Two Google Drive folders (for TXT and Google Docs)

### 1. Setup Environment Variables

Create a `.env.yaml` file:

```yaml
NOTION_API_KEY: "your_notion_api_key"
NOTION_PAGE_ID: "default_page_id_optional" 
DRIVE_FOLDER_ID: "your_txt_folder_id"
GDOC_FOLDER_ID: "your_gdoc_folder_id"
NOTION_VERIFICATION_TOKEN: "your_webhook_secret"
```

### 2. Deploy to Google Cloud Functions

```bash
# Install dependencies
pip install -r requirements.txt

# Deploy the function
gcloud functions deploy sync_notion_to_drive \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --env-vars-file .env.yaml \
  --gen2 \
  --region=us-central1
```

### 3. Configure Notion Integration

1. Create a Notion integration at [notion.so/my-integrations](https://notion.so/my-integrations)
2. Get your API key and add it to `.env.yaml`
3. Share your Notion pages with the integration
4. Set up a webhook pointing to your Cloud Function URL

## 📋 Example Output

### Metadata Section
```
Title: Project Planning Document
Notion Page ID: 1234567890abcdef
Last Synced: January 25, 2025 5:17 PM PT

== Page Properties ==
Priority: High
Due Date: January 30, 2025 to February 15, 2025
Assigned To: John Doe, Jane Smith
Status: In Progress
Tags: urgent, marketing, q1-2025
Budget: 15000
Completed: No

== Page Info ==
Created: January 20, 2025 10:30 AM PT
Last Edited: January 25, 2025 2:15 PM PT
Created By: Alice Johnson
Last Edited By: Bob Wilson
Notion URL: https://notion.so/...
---
[Your page content follows...]
```

## 🏗️ Architecture

```
Notion Page → Webhook → Cloud Function → {
  ├── Extract comprehensive metadata
  ├── Process all blocks and content  
  ├── Generate TXT file → Drive Folder A
  └── Generate Google Doc → Drive Folder B
}
```

## 🔧 Configuration Options

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `NOTION_API_KEY` | Your Notion integration API key | Yes |
| `DRIVE_FOLDER_ID` | Google Drive folder ID for TXT files | Yes |
| `GDOC_FOLDER_ID` | Google Drive folder ID for Google Docs | Yes |
| `NOTION_VERIFICATION_TOKEN` | Webhook signature verification | Optional |
| `NOTION_PAGE_ID` | Default page ID fallback | Optional |

### Supported Notion Content Types

- **Text Blocks**: Paragraphs, headings (H1-H3), quotes
- **Lists**: Bulleted and numbered lists  
- **Code Blocks**: Preserved formatting
- **Dividers**: Converted to horizontal rules
- **Nested Content**: Full hierarchy support

## 📝 API Usage

### Webhook Payload

The function accepts Notion webhook payloads and manual triggers:

```json
{
  "page": {
    "id": "your-page-id"
  }
}
```

### Response

```json
{
  "status": "started",
  "message": "Sync started successfully! Please wait 10-30 seconds for the documents to appear in your Drive folders."
}
```

## 🔍 Monitoring

### Logs
- View logs in [Google Cloud Console](https://console.cloud.google.com/functions)
- Detailed debugging information included
- Background sync progress tracking

### Error Handling
- Graceful fallbacks for all operations
- Always returns 200 status to prevent Notion errors
- Comprehensive error logging

## 🛠️ Development

### Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export NOTION_API_KEY="your_key"
export DRIVE_FOLDER_ID="folder_id"
# ... other vars

# Test the function locally
functions-framework --target=sync_notion_to_drive --debug
```

### File Structure

```
├── main.py              # Main Cloud Function code
├── requirements.txt     # Python dependencies
├── .env.yaml           # Environment variables
└── README.md           # This file
```

## 📦 Dependencies

- `functions-framework` - Google Cloud Functions runtime
- `notion-client` - Official Notion API client
- `google-auth` & `google-api-python-client` - Google APIs
- `pytz` - Timezone handling
- `requests` - HTTP requests

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🆘 Support

- Check the [Google Cloud Functions documentation](https://cloud.google.com/functions/docs)
- Review [Notion API documentation](https://developers.notion.com)
- Open an issue for bugs or feature requests


