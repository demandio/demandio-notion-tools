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

**[→ View Full Documentation](./notion-drive-sync/README.md)**

## 📋 Repository Structure

```
demandio-notion-tools/
├── README.md                    # This file - repository overview
└── notion-drive-sync/           # Notion to Google Drive sync tool
    ├── README.md                # Detailed documentation
    ├── main.py                  # Cloud Function code
    ├── requirements.txt         # Python dependencies
    └── env.example.yaml         # Environment variables template
```

## 🚀 Quick Start

Each tool has its own directory with complete documentation. Navigate to the specific tool folder for detailed setup instructions.

## 🤝 Contributing

1. Fork this repository
2. Create a feature branch for your tool/enhancement
3. Add your tool in a new directory with comprehensive documentation
4. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

---

**Made with ❤️ by the DemandIO team** 