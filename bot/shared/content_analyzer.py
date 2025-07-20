#!/usr/bin/env python3
"""
Content analysis for transfer news
"""

import re
from typing import Dict, List

# Tier 1 sources (from our analysis)
TIER_1_SOURCES = [
    'fabrizio romano', 'david ornstein', 'sky sports', 'the athletic', 
    'guardian', 'bbc sport', 'florian plettenberg'
]

TIER_2_SOURCES = [
    'di marzio', 'bild', 'kicker', 'sport bild', 'marca', 'as'
]

# High confidence formats
HIGH_CONFIDENCE_FORMATS = [
    '📝 deal done', '🚨 official', 'here we go', '🚨 breaking', '🚨 confirmed'
]

# Transfer keywords
TRANSFER_KEYWORDS = [
    'transfer', 'signing', 'signs', 'joins', 'agreement', 'deal', 'contract',
    'move', 'bid', 'offer', 'target', 'medical', 'done deal', 'official', 
    'confirmed', 'breaking', 'exclusive', 'loan', 'release clause'
]

# Spam indicators
SPAM_INDICATORS = [
    't.me/+', 'betting', 'casino', 'place your bets', 'promo code',
    'free spins', 'bonus', 'click here', 'register now'
]

class ContentAnalyzer:
    """Analyzes transfer news content for quality and relevance"""
    
    def is_spam(self, text: str) -> bool:
        """Check if message is spam"""
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in SPAM_INDICATORS)
    
    def get_source_tier(self, text: str) -> int:
        """Get source tier (1=best, 3=worst)"""
        text_lower = text.lower()
        
        for source in TIER_1_SOURCES:
            if source in text_lower:
                return 1
                
        for source in TIER_2_SOURCES:
            if source in text_lower:
                return 2
                
        return 3
    
    def get_confidence_level(self, text: str) -> str:
        """Get confidence level based on format"""
        text_lower = text.lower()
        
        for format_indicator in HIGH_CONFIDENCE_FORMATS:
            if format_indicator in text_lower:
                return 'high'
                
        if any(keyword in text_lower for keyword in TRANSFER_KEYWORDS):
            return 'medium'
            
        return 'low'
    
    def is_transfer_related(self, text: str) -> bool:
        """Check if content is transfer related"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in TRANSFER_KEYWORDS)
    
    def should_post(self, text: str, clubs_detected: List[str]) -> bool:
        """Main filtering logic"""
        # Skip spam
        if self.is_spam(text):
            return False
            
        # Must mention our target clubs
        if not clubs_detected:
            return False
            
        # Must be transfer related
        if not self.is_transfer_related(text):
            return False
            
        # Check source quality
        source_tier = self.get_source_tier(text)
        confidence = self.get_confidence_level(text)
        
        # High confidence posts - allow Tier 1 & 2
        if confidence == 'high':
            return source_tier <= 2
            
        # Medium confidence - only Tier 1
        if confidence == 'medium':
            return source_tier == 1
            
        # Low confidence - skip
        return False