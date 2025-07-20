#!/usr/bin/env python3
"""
Main transfer bot orchestrator
"""

import asyncio
import logging
from typing import Dict, Any

from .sources.telegram_source import TelegramSource
from .shared.club_configs import CLUB_CONFIGS, detect_clubs
from .shared.content_analyzer import ContentAnalyzer
from .shared.discord_sender import DiscordSender
from .shared.storage import MessageStorage
from .config.settings import settings

logger = logging.getLogger(__name__)

class TransferBot:
    """Main transfer news bot"""
    
    def __init__(self):
        self.source = None
        self.analyzer = ContentAnalyzer()
        self.discord_sender = DiscordSender(settings.DISCORD_WEBHOOKS)
        self.storage = MessageStorage(settings.SEEN_MESSAGES_FILE)
        
    async def initialize(self):
        """Initialize bot components"""
        logger.info("🚀 Initializing Transfer Bot...")
        
        # Validate settings
        settings.validate()
        
        # Initialize source
        if settings.SOURCE_TYPE == 'telegram':
            self.source = TelegramSource(
                api_id=settings.TELEGRAM_API_ID,
                api_hash=settings.TELEGRAM_API_HASH,
                phone=settings.TELEGRAM_PHONE,
                channel_username=settings.TELEGRAM_CHANNEL,
                club_configs=CLUB_CONFIGS,
                seen_storage=self.storage
            )
        else:
            raise ValueError(f"Unsupported source type: {settings.SOURCE_TYPE}")
            
        # Connect to source
        await self.source.connect()
        
        # Load seen messages
        self.storage.load()
        
        logger.info("✅ Bot initialized successfully")
    
    async def process_message(self, message_data: Dict[str, Any]) -> bool:
        """Process a single message"""
        message_id = message_data['id']
        text = message_data['text']
        
        # Skip if already seen
        if self.storage.is_seen(message_id):
            return False
            
        # Detect clubs
        clubs_detected = detect_clubs(text)
        
        # Apply filtering logic
        should_post = self.analyzer.should_post(text, clubs_detected)
        
        # Mark as seen regardless
        self.storage.mark_seen(message_id)
        
        if not should_post:
            return False
            
        # Post to Discord
        for club_key in clubs_detected:
            if club_key in CLUB_CONFIGS:
                # Add analysis to message data
                message_data['source_tier'] = f"Tier {self.analyzer.get_source_tier(text)}"
                message_data['confidence'] = self.analyzer.get_confidence_level(text)
                
                success = self.discord_sender.send_message(
                    message_data, 
                    club_key, 
                    CLUB_CONFIGS[club_key]
                )
                
                if success:
                    logger.info(f"✅ Posted: {club_key} - {text[:50]}...")
                    
        return True
    
    async def find_first_sendable_message(self, max_limit: int = 50):
        """Find and post the first sendable message from recent history"""
        logger.info("🔍 Finding first sendable message...")
        
        for check_limit in range(1, max_limit + 1):
            messages = await self.source.fetch_recent_messages(check_limit)
            
            # Check messages from oldest to newest (reversed order)
            for message_data in reversed(messages):
                if not self.storage.is_seen(message_data['id']):
                    if await self.process_message(message_data):
                        logger.info(f"✅ Posted startup message after checking {check_limit} recent messages")
                        return True
                        
        logger.info(f"ℹ️ No sendable messages found in last {max_limit} messages")
        return False

    async def run_initial_check(self):
        """Check recent messages on startup"""
        await self.find_first_sendable_message()
        self.storage.save()
    
    async def start_monitoring(self):
        """Start real-time monitoring"""
        logger.info("📡 Starting real-time monitoring...")
        
        try:
            await self.source.start_monitoring(self.process_message)
        except Exception as e:
            logger.error(f"❌ Monitoring error: {e}")
            raise
    
    async def run(self):
        """Main run method"""
        try:
            await self.initialize()
            await self.run_initial_check()
            await self.start_monitoring()
            
        except KeyboardInterrupt:
            logger.info("🛑 Bot stopped by user")
        except Exception as e:
            logger.error(f"❌ Bot error: {e}")
            raise
        finally:
            self.storage.save()
            if self.source:
                await self.source.disconnect()
            logger.info("💾 Bot shutdown complete")