#!/usr/bin/env python3
"""
Message storage for tracking seen messages
"""

import json
import logging
from typing import Set

logger = logging.getLogger(__name__)

class MessageStorage:
    """Handles storage of seen message IDs"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.seen_messages: Set[str] = set()
        
    def load(self):
        """Load seen messages from file"""
        try:
            with open(self.file_path, 'r') as f:
                seen_list = json.load(f)
                self.seen_messages = set(seen_list)
                logger.info(f"📋 Loaded {len(self.seen_messages)} seen messages")
        except FileNotFoundError:
            logger.info("📋 No previous seen messages file, starting fresh")
        except json.JSONDecodeError:
            logger.warning("⚠️ Error reading seen messages file, starting fresh")
            
    def save(self):
        """Save seen messages to file"""
        seen_list = list(self.seen_messages)
        # Keep only most recent 2000 to prevent file growth
        if len(seen_list) > 2000:
            seen_list = seen_list[-2000:]
            self.seen_messages = set(seen_list)
            
        with open(self.file_path, 'w') as f:
            json.dump(seen_list, f, indent=2)
            
    def is_seen(self, message_id: str) -> bool:
        """Check if message has been seen"""
        return message_id in self.seen_messages
        
    def mark_seen(self, message_id: str):
        """Mark message as seen"""
        self.seen_messages.add(message_id)
        
        # Periodic save
        if len(self.seen_messages) % 20 == 0:
            self.save()