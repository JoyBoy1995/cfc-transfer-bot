#!/usr/bin/env python3
"""
Club configurations and matching logic
"""

# Club configurations (extracted from reddit_bot.py)
CLUB_CONFIGS = {
    'chelsea': {
        'name': 'Chelsea FC',
        'emoji': '🔵',
        'color': 0x034694,
        'logo': 'https://logos-world.net/wp-content/uploads/2020/06/Chelsea-Logo.png',
        'keywords': ['chelsea', 'cfc', 'blues', 'stamford bridge']
    },
    'arsenal': {
        'name': 'Arsenal FC', 
        'emoji': '🔴',
        'color': 0xEF0107,
        'logo': 'https://logos-world.net/wp-content/uploads/2020/06/Arsenal-Logo.png',
        'keywords': ['arsenal', 'afc', 'gunners', 'emirates']
    },
    'tottenham': {
        'name': 'Tottenham Hotspur',
        'emoji': '⚪', 
        'color': 0x132257,
        'logo': 'https://logos-world.net/wp-content/uploads/2020/11/Tottenham-Logo.png',
        'keywords': ['tottenham', 'spurs', 'thfc', 'coys', 'white hart lane']
    },
    'man_united': {
        'name': 'Manchester United',
        'emoji': '🔴',
        'color': 0xDA020E, 
        'logo': 'https://logos-world.net/wp-content/uploads/2020/06/Manchester-United-Logo.png',
        'keywords': ['manchester united', 'man united', 'man utd', 'mufc', 'red devils', 'old trafford']
    },
    'man_city': {
        'name': 'Manchester City',
        'emoji': '🔵',
        'color': 0x6CABDD,
        'logo': 'https://logos-world.net/wp-content/uploads/2020/06/Manchester-City-Logo.png',
        'keywords': ['manchester city', 'man city', 'mcfc', 'city', 'citizens', 'etihad']
    },
    'real_madrid': {
        'name': 'Real Madrid',
        'emoji': '⚪',
        'color': 0xFFFFFF,
        'logo': 'https://logos-world.net/wp-content/uploads/2020/06/Real-Madrid-Logo.png',
        'keywords': ['real madrid', 'madrid', 'real', 'los blancos', 'bernabeu']
    },
    'barcelona': {
        'name': 'Barcelona',
        'emoji': '🔴',
        'color': 0xA50044,
        'logo': 'https://logos-world.net/wp-content/uploads/2020/06/Barcelona-Logo.png', 
        'keywords': ['barcelona', 'barca', 'barça', 'fcb', 'blaugrana', 'camp nou']
    }
}

def detect_clubs(text: str) -> list:
    """Detect which clubs are mentioned in text"""
    text_lower = text.lower()
    clubs_found = []
    
    for club_key, config in CLUB_CONFIGS.items():
        for keyword in config['keywords']:
            if keyword in text_lower:
                clubs_found.append(club_key)
                break
                
    return clubs_found