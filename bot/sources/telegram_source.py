#!/usr/bin/env python3
"""
Telegram source for transfer news
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Callable
from telethon import TelegramClient
from .base import TransferSource

logger = logging.getLogger(__name__)

class TelegramSource(TransferSource):
    """Telegram channel source for transfer news"""
    
    def __init__(self, api_id: int, api_hash: str, phone: str, channel_username: str, club_configs: Dict, seen_storage):
        super().__init__(club_configs, seen_storage)
        self.api_id = api_id
        self.api_hash = api_hash  
        self.phone = phone
        self.channel_username = channel_username
        self.client = None
        
    async def connect(self):
        """Connect to Telegram"""
        logger.info("🔗 Connecting to Telegram...")
        self.client = TelegramClient('session', self.api_id, self.api_hash)
        await self.client.start(phone=self.phone)
        logger.info("✅ Connected to Telegram")
        
    async def fetch_recent_messages(self, limit: int = 1):
        """Fetch recent messages for initial check"""
        logger.info(f"📥 Fetching last {limit} messages from @{self.channel_username}")
        
        try:
            channel = await self.client.get_entity(self.channel_username)
            messages = []
            
            async for message in self.client.iter_messages(channel, limit=limit):
                if message.text:
                    parsed = self.parse_message(message)
                    messages.append(parsed)
                    
            logger.info(f"✅ Fetched {len(messages)} messages")
            return messages
            
        except Exception as e:
            logger.error(f"❌ Error fetching messages: {e}")
            return []
    
    async def start_monitoring(self, message_callback: Callable):
        """Start real-time monitoring"""
        logger.info(f"👀 Starting live monitoring of @{self.channel_username}")
        
        try:
            from telethon import events
            
            # Get channel entity
            channel = await self.client.get_entity(self.channel_username)
            
            # Define event handler for new messages
            @self.client.on(events.NewMessage(chats=channel))
            async def handler(event):
                if event.message.text:
                    parsed = self.parse_message(event.message)
                    await message_callback(parsed)
            
            logger.info("✅ Real-time monitoring started - waiting for new messages...")
            
            # Keep the client running
            await self.client.run_until_disconnected()
                    
        except Exception as e:
            logger.error(f"❌ Monitoring error: {e}")
            raise
    
    def parse_message(self, message) -> Dict[str, Any]:
        """Parse Telegram message into standardized format"""
        # Clean up the message text by removing broken telegra.ph links
        clean_text = message.text
        if clean_text:
            # Remove telegra.ph link patterns like [​​](https://telegra.ph/file/...)
            import re
            clean_text = re.sub(r'\[​​\]\(https://telegra\.ph/file/[^)]+\)', '', clean_text)
            clean_text = clean_text.strip()
        
        return {
            'id': str(message.id),
            'text': clean_text,
            'title': clean_text[:200] if clean_text else '',  # First 200 chars as title
            'timestamp': message.date.isoformat(),
            'views': getattr(message, 'views', 0) or 0,
            'source_name': 'Telegram',
            'source_url': f"https://t.me/{self.channel_username}/{message.id}",
            'raw_message': message
        }
    
    async def disconnect(self):
        """Disconnect from Telegram"""
        if self.client:
            await self.client.disconnect()
            logger.info("👋 Disconnected from Telegram")