# README.md
# Chelsea Reddit Transfer Bot

Monitors r/chelseafc for Tier 1 and Tier 2 transfer posts and sends them to Discord.

## Setup Instructions

### 1. Reddit App Setup
1. Go to https://reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Fill out the form:
   - name: discord_cfc (or any name)
   - App type: script
   - description: Discord bot for Chelsea transfer news
   - about url: (leave blank)
   - redirect uri: http://localhost:8080
4. Click "create app"
5. Note down your client ID (short string under app name) and client secret

### 2. Discord Webhook Setup
1. Go to your Discord server
2. Server Settings → Integrations → Webhooks
3. Create New Webhook → Choose your channel
4. Copy the Webhook URL

### 3. Environment Setup
1. Create a `.env` file in your project directory
2. Add your credentials to the `.env` file (see .env template above)
sure
### 4. Installation
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
.\venv\Scripts\Activate.ps1
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 5. Run the Bot
```bash
python reddit_bot.py
```

## How It Works

- Monitors r/chelseafc for new posts in real-time
- Only posts submissions with "Tier 1" or "Tier 2" link flair
- Prevents duplicate posts by tracking seen submissions
- Posts rich embeds to Discord with source links and discussion links
- Handles connection errors and automatically reconnects

## Features

- ✅ Real-time monitoring of r/chelseafc
- ✅ Filters for Tier 1 and Tier 2 reliability flairs only
- ✅ Rich Discord embeds with source and Reddit links
- ✅ Duplicate prevention
- ✅ Automatic reconnection on errors
- ✅ Comprehensive logging
- ✅ Checks recent posts on startup (won't miss anything)

## Stopping the Bot

Press `Ctrl+C` to stop the bot. It will save its state before exiting.