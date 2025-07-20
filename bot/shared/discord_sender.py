#!/usr/bin/env python3
"""
Discord webhook sender (extracted from reddit_bot.py)
"""

import requests
import logging
from datetime import datetime
from typing import Dict, List

logger = logging.getLogger(__name__)

class DiscordSender:
    """Handles Discord webhook posting"""
    
    def __init__(self, webhook_urls: List[str]):
        self.webhook_urls = webhook_urls
    
    def send_message(self, message_data: Dict, club_key: str, club_config: Dict) -> bool:
        """Send message to Discord webhooks"""
        
        # Create clean embed
        embed = {
            "title": f"{club_config['emoji']} {club_config['name']}",
            "description": message_data['title'],
            "color": club_config['color'],
            "timestamp": message_data.get('timestamp', datetime.now().isoformat()),
            "footer": {
                "text": f"Transfer Bot • {message_data.get('source_name', 'Telegram')}"
            }
        }
        
        payload = {"embeds": [embed]}
        
        # Send to all webhooks
        success_count = 0
        for webhook_url in self.webhook_urls:
            try:
                response = requests.post(
                    webhook_url,
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                
                if response.status_code == 204:
                    success_count += 1
                else:
                    logger.error(f"Discord webhook failed: {response.status_code}")
                    
            except requests.RequestException as e:
                logger.error(f"Error posting to Discord webhook: {e}")
        
        if success_count > 0:
            logger.info(f"Posted to {success_count}/{len(self.webhook_urls)} Discord channels")
            return True
        else:
            logger.error("Failed to post to any Discord channels")
            return False