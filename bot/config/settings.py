#!/usr/bin/env python3
"""
Bot configuration settings
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Bot configuration settings"""
    
    # Telegram settings
    TELEGRAM_API_ID = int(os.getenv('TELEGRAM_API_ID', 0))
    TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH', '').strip('"\'')
    TELEGRAM_PHONE = os.getenv('TELEGRAM_PHONE', '').strip('"\'')
    TELEGRAM_CHANNEL = os.getenv('TELEGRAM_CHANNEL', 'transfer_news_football').strip('"\'')
    
    def __init__(self):
        print(f"DEBUG - API_ID: {self.TELEGRAM_API_ID}")
        print(f"DEBUG - API_HASH: {self.TELEGRAM_API_HASH[:8]}...")
        print(f"DEBUG - PHONE: {self.TELEGRAM_PHONE}")
        print(f"DEBUG - WEBHOOK COUNT: {len(self.DISCORD_WEBHOOKS)}")
    
    # Discord settings
    DISCORD_WEBHOOKS = [
        url.strip() 
        for url in os.getenv('DISCORD_WEBHOOK_URL', '').split(',') 
        if url.strip()
    ]
    
    # Storage settings
    SEEN_MESSAGES_FILE = os.getenv('SEEN_MESSAGES_FILE', '/tmp/seen_messages.json')
    
    # Bot settings
    SOURCE_TYPE = os.getenv('SOURCE_TYPE', 'telegram')  # 'telegram' or 'reddit'
    INITIAL_CHECK_LIMIT = int(os.getenv('INITIAL_CHECK_LIMIT', 50))
    
    def validate(self):
        """Validate required settings"""
        if self.SOURCE_TYPE == 'telegram':
            if not all([self.TELEGRAM_API_ID, self.TELEGRAM_API_HASH, self.TELEGRAM_PHONE]):
                raise ValueError("Missing Telegram credentials")
                
        if not self.DISCORD_WEBHOOKS:
            raise ValueError("Missing Discord webhook URLs")

# Global settings instance
settings = Settings()