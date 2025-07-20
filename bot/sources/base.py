#!/usr/bin/env python3
"""
Abstract base class for transfer news sources
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class TransferSource(ABC):
    """Abstract base class for transfer news sources"""
    
    def __init__(self, club_configs: Dict, seen_storage):
        self.club_configs = club_configs
        self.seen_storage = seen_storage
        
    @abstractmethod
    async def connect(self):
        """Connect to the source"""
        pass
        
    @abstractmethod
    async def fetch_recent_messages(self, limit: int = 50):
        """Fetch recent messages for initial check"""
        pass
        
    @abstractmethod
    async def start_monitoring(self, message_callback):
        """Start real-time monitoring with callback for new messages"""
        pass
        
    @abstractmethod
    def parse_message(self, raw_message) -> Dict[str, Any]:
        """Parse raw message into standardized format"""
        pass
        
    @abstractmethod
    async def disconnect(self):
        """Cleanup and disconnect"""
        pass