# DemandIO Notion Tools

A collection of tools and integrations for enhancing Notion workflows at DemandIO.

## 🛠️ Tools

### 📁 [Notion to Google Drive Sync](./notion-drive-sync/)

A robust Google Cloud Function that automatically syncs your Notion pages to Google Drive in multiple formats.

**Features:**
- 🔄 Webhook-triggered sync from Notion pages
- 📄 Dual format output (TXT files + Google Docs)
- 🏷️ Comprehensive metadata extraction from all Notion property types
- 🎯 Organized storage in separate Drive folders
- 🔒 Enterprise-ready with authentication and error handling

### 🤖 [Slack Grounding Recommendations](./slack-grounding-recommendations/)

A serverless Python application that monitors Slack conversations and suggests updates to Notion documentation when it detects potential conflicts or outdated information.

**Features:**
- 🔄 Weekly automated monitoring of Slack channels and Notion pages
- 🤖 AI-powered analysis using Claude to identify conflicts and suggest updates
- 🔗 Direct deep-links to specific Notion blocks that need updating
- 📧 Automatic notification of document owners via Slack

## 📋 Repository Structure

```
demandio-notion-tools/
├── README.md                    # This file - repository overview
├── shared/                      # Shared utilities across tools
│   ├── __init__.py             # Package initialization
│   └── env.py                  # Shared environment handling
├── notion-drive-sync/          # Notion to Google Drive sync tool
│   ├── README.md               # Tool-specific documentation
│   ├── main.py                 # Cloud Function code
│   └── requirements.txt        # Python dependencies
└── slack-grounding-recommendations/  # Slack monitoring tool
    ├── README.md               # Tool-specific documentation
    ├── main.py                 # Cloud Function code
    └── requirements.txt        # Python dependencies
```

## 🔐 Environment Variables

This repository uses a two-level approach to environment variables:

1. **Root Level** (`.env` in repository root):
   ```
   # Shared API Keys
   NOTION_API_KEY=your-notion-api-key
   GOOGLE_CLOUD_PROJECT=your-gcp-project-id
   ```

2. **Tool Level** (`.env` in tool directories):
   ```
   # Tool-specific variables
   GOOGLE_DRIVE_FOLDER_ID=your-drive-folder-id  # notion-drive-sync
   SLACK_BOT_TOKEN=your-slack-token             # slack-grounding
   ANTHROPIC_API_KEY=your-claude-key            # slack-grounding
   ```

The shared `env.py` module handles loading these variables with the following priority:
1. Tool-specific `.env` file (highest priority)
2. Root `.env` file (fallback for shared variables)
3. System environment variables (lowest priority)

### Usage in Code

```python
from shared.env import load_tool_env, get_notion_api_key

# Load tool-specific environment (will also load root .env)
load_tool_env('your-tool-name')

# Get shared variables
notion_key = get_notion_api_key()
```

## 🚀 Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/demandio/demandio-notion-tools.git
   cd demandio-notion-tools
   ```

2. Create root `.env` file with shared variables:
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

3. Navigate to specific tool directory and follow its README for setup:
   ```bash
   cd notion-drive-sync  # or slack-grounding-recommendations
   # Follow tool-specific README.md
   ```

## 🤝 Contributing

1. Fork this repository
2. Create a feature branch for your tool/enhancement
3. Add your tool in a new directory with comprehensive documentation
4. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

---

**Made with ❤️ by the DemandIO team** 