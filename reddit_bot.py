#!/usr/bin/env python3
"""
Multi-Club Reddit Transfer Bot
Monitors multiple football subreddits for Tier 1 and Tier 2 transfer posts and sends to Discord
"""

import praw
import requests
import json
import time
import os
from datetime import datetime
from dotenv import load_dotenv
from typing import Set, Dict, List
import logging

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MultiClubRedditBot:
    def __init__(self):
        # Reddit API credentials from environment variables
        self.reddit_client_id = os.getenv('REDDIT_CLIENT_ID')
        self.reddit_client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        self.reddit_user_agent = os.getenv('REDDIT_USER_AGENT', 'multi_club_bot/1.0')

        # Discord webhooks - can be multiple separated by commas
        discord_webhooks_env = os.getenv('DISCORD_WEBHOOK_URL', '')
        self.discord_webhooks = [url.strip() for url in discord_webhooks_env.split(',') if url.strip()]

        # Validate required environment variables
        if not all([self.reddit_client_id, self.reddit_client_secret]) or not self.discord_webhooks:
            raise ValueError("Missing required environment variables. Check your .env file.")

        # File to store seen submissions (use persistent path for Railway)
        self.seen_file = '/tmp/seen_submissions.json'
        self.seen_submissions: Set[str] = set()

        # Target flairs - only high quality sources
        self.target_flairs = ['Tier 1', 'Tier 2', 'Official Source']

        # Club configurations
        self.clubs = {
            'chelseafc': {
                'name': 'Chelsea FC',
                'emoji': '🔵',
                'color': 0x034694,  # Chelsea blue
                'logo': 'https://logos-world.net/wp-content/uploads/2020/06/Chelsea-Logo.png'
            },
            'realmadrid': {
                'name': 'Real Madrid',
                'emoji': '⚪',
                'color': 0xFFFFFF,  # White
                'logo': 'https://logos-world.net/wp-content/uploads/2020/06/Real-Madrid-Logo.png'
            },
            'coys': {
                'name': 'Tottenham Hotspur',
                'emoji': '⚪',
                'color': 0x132257,  # Navy blue
                'logo': 'https://logos-world.net/wp-content/uploads/2020/11/Tottenham-Logo.png'
            },
            'gunners': {
                'name': 'Arsenal FC',
                'emoji': '🔴',
                'color': 0xEF0107,  # Arsenal red
                'logo': 'https://logos-world.net/wp-content/uploads/2020/06/Arsenal-Logo.png'
            },
            'liverpoolfc': {
                'name': 'Liverpool FC',
                'emoji': '🔴',
                'color': 0xC8102E,  # Liverpool red
                'logo': 'https://logos-world.net/wp-content/uploads/2020/06/Liverpool-Logo.png'
            },
            'mcfc': {
                'name': 'Manchester City',
                'emoji': '🔵',
                'color': 0x6CABDD,  # City blue
                'logo': 'https://logos-world.net/wp-content/uploads/2020/06/Manchester-City-Logo.png'
            },
            'reddevils': {
                'name': 'Manchester United',
                'emoji': '🔴',
                'color': 0xDA020E,  # United red
                'logo': 'https://logos-world.net/wp-content/uploads/2020/06/Manchester-United-Logo.png'
            },
            'soccer': {
                'name': 'General Football',
                'emoji': '⚽',
                'color': 0x00FF00,  # Green for general
                'logo': 'https://cdn-icons-png.flaticon.com/512/53/53283.png'
            }
        }

        # Initialize Reddit instance
        self.reddit = None

    def connect_to_reddit(self):
        """Initialize Reddit connection"""
        try:
            self.reddit = praw.Reddit(
                client_id=self.reddit_client_id,
                client_secret=self.reddit_client_secret,
                user_agent=self.reddit_user_agent
            )

            # Test connection with Chelsea subreddit
            test_subreddit = self.reddit.subreddit('chelseafc')
            logger.info(f"✅ Connected to Reddit. Testing with r/chelseafc: {test_subreddit.subscribers:,} subscribers")

        except Exception as e:
            logger.error(f"❌ Failed to connect to Reddit: {e}")
            raise

    def load_seen_submissions(self):
        """Load previously seen submissions from file"""
        try:
            with open(self.seen_file, 'r') as f:
                seen_list = json.load(f)
                self.seen_submissions = set(seen_list)
                logger.info(f"📋 Loaded {len(self.seen_submissions)} seen submissions")
        except FileNotFoundError:
            logger.info("📋 No previous seen submissions file, starting fresh")
            self.seen_submissions = set()
        except json.JSONDecodeError:
            logger.warning("⚠️ Error reading seen submissions file, starting fresh")
            self.seen_submissions = set()

    def save_seen_submissions(self):
        """Save seen submissions to file"""
        seen_list = list(self.seen_submissions)
        # Keep only the most recent 2000 to prevent file from growing too large
        if len(seen_list) > 2000:
            seen_list = seen_list[-2000:]
            self.seen_submissions = set(seen_list)

        with open(self.seen_file, 'w') as f:
            json.dump(seen_list, f, indent=2)

    def is_transfer_related(self, title: str, text: str = '') -> bool:
        """Check if post is transfer related"""
        content = f"{title} {text}".lower()
        transfer_keywords = [
            'transfer', 'signing', 'signs', 'joins', 'agreement', 'deal',
            'contract', 'move', 'bid', 'offer', 'target', 'rumour', 'rumor',
            'exclusive', 'breaking', 'confirmed', 'announces', 'loan',
            'release clause', 'medical', 'here we go', 'done deal',
            'official', 'unveil', 'welcome', 'new signing'
        ]

        return any(keyword in content for keyword in transfer_keywords)

    def send_to_discord(self, submission, club_key: str):
        """Send submission to Discord via webhook(s)"""
        club_info = self.clubs[club_key]

        # Determine tier and color
        tier = submission.link_flair_text or "News"
        color = club_info['color']

        # Get submission details
        title = submission.title
        url = submission.url
        reddit_url = f"https://reddit.com{submission.permalink}"
        author = str(submission.author) if submission.author else "Unknown"
        created_time = datetime.fromtimestamp(submission.created_utc)

        # Truncate title if too long
        if len(title) > 200:
            title = title[:197] + "..."

        # Create embed
        embed = {
            "title": f"{club_info['emoji']} {tier} - {club_info['name']}",
            "description": title,
            "color": color,
            "fields": [
                {
                    "name": "Source",
                    "value": f"[View Article]({url})",
                    "inline": True
                },
                {
                    "name": "Reddit Discussion",
                    "value": f"[r/{club_key}]({reddit_url})",
                    "inline": True
                },
                {
                    "name": "Posted by",
                    "value": f"u/{author}",
                    "inline": True
                },
                {
                    "name": "Tier",
                    "value": tier,
                    "inline": True
                },
                {
                    "name": "Subreddit",
                    "value": f"r/{club_key}",
                    "inline": True
                }
            ],
            "timestamp": created_time.isoformat(),
            "footer": {
                "text": f"Multi-Club Transfer Bot • r/{club_key}"
            },
            "thumbnail": {
                "url": club_info['logo']
            }
        }

        # Add score field if this is from r/soccer
        if club_key == 'soccer':
            embed["fields"].append({
                "name": "Score",
                "value": f"↑ {submission.score}",
                "inline": True
            })

        payload = {
            "embeds": [embed]
        }

        # Send to all configured webhooks
        success_count = 0
        for webhook_url in self.discord_webhooks:
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
                    logger.error(f"❌ Discord webhook failed: {response.status_code} for {webhook_url[:50]}...")

            except requests.RequestException as e:
                logger.error(f"❌ Error posting to Discord webhook {webhook_url[:50]}...: {e}")

        if success_count > 0:
            logger.info(
                f"✅ Posted to {success_count}/{len(self.discord_webhooks)} Discord channels: [{club_info['name']}] {title[:50]}...")
            return True
        else:
            logger.error(f"❌ Failed to post to any Discord channels")
            return False

    def process_submission(self, submission, club_key: str):
        """Process a single submission"""
        # Skip if already seen
        if submission.id in self.seen_submissions:
            return False

        # For club-specific subreddits, ONLY check flair (strict filtering)
        if club_key != 'soccer':
            # Must have Tier 1, Tier 2, or Official Source flair
            if submission.link_flair_text not in self.target_flairs:
                self.seen_submissions.add(submission.id)
                return False
        else:
            # For r/soccer, check transfer keywords AND require high score
            if not self.is_transfer_related(submission.title, getattr(submission, 'selftext', '')):
                self.seen_submissions.add(submission.id)
                return False

            # Only post r/soccer posts with high upvotes AND tier flair if available
            if submission.score < 100:  # Increased threshold
                self.seen_submissions.add(submission.id)
                return False

            # If r/soccer post has a flair, it must be a good one
            if submission.link_flair_text and submission.link_flair_text not in self.target_flairs:
                # Skip if it has a flair but it's not Tier 1/2/Official
                if 'tier' in submission.link_flair_text.lower():
                    self.seen_submissions.add(submission.id)
                    return False

        # Log the submission
        tier = submission.link_flair_text or "News"
        logger.info(f"📢 Found {tier} post in r/{club_key}: {submission.title[:50]}...")

        # Send to Discord
        success = self.send_to_discord(submission, club_key)

        # Mark as seen regardless of Discord success
        self.seen_submissions.add(submission.id)

        # Save seen submissions periodically
        if len(self.seen_submissions) % 20 == 0:
            self.save_seen_submissions()

        return success

    def check_recent_posts(self, club_key: str, limit: int = 10):
        """Check recent posts for any missed Tier 1/2 posts"""
        logger.info(f"🔍 Checking last {limit} posts in r/{club_key}...")

        try:
            subreddit = self.reddit.subreddit(club_key)
            found_count = 0

            for submission in subreddit.new(limit=limit):
                if self.process_submission(submission, club_key):
                    found_count += 1
                    time.sleep(1)  # Small delay between Discord posts

            if found_count > 0:
                logger.info(f"✅ Posted {found_count} items from r/{club_key}")

        except Exception as e:
            logger.error(f"❌ Error checking r/{club_key}: {e}")

    def monitor_subreddit(self, club_key: str):
        """Monitor a single subreddit for new posts"""
        logger.info(f"👀 Monitoring r/{club_key}...")

        try:
            subreddit = self.reddit.subreddit(club_key)
            for submission in subreddit.stream.submissions(skip_existing=True):
                self.process_submission(submission, club_key)
        except Exception as e:
            logger.error(f"❌ Stream error for r/{club_key}: {e}")
            raise

    def monitor_all_subreddits(self):
        """Monitor all configured subreddits"""
        logger.info("🚀 Starting live monitoring of all subreddits...")

        while True:
            try:
                # Create a multireddit string
                subreddit_names = '+'.join(self.clubs.keys())
                multireddit = self.reddit.subreddit(subreddit_names)

                logger.info(f"📡 Monitoring: {subreddit_names}")

                for submission in multireddit.stream.submissions(skip_existing=True):
                    # Determine which subreddit this came from
                    club_key = submission.subreddit.display_name.lower()

                    # Skip if we don't have config for this subreddit
                    if club_key not in self.clubs:
                        continue

                    self.process_submission(submission, club_key)

            except Exception as e:
                logger.error(f"❌ Stream error: {e}")
                logger.info("🔄 Reconnecting in 30 seconds...")
                time.sleep(30)

                # Try to reconnect to Reddit
                try:
                    self.connect_to_reddit()
                except Exception as reconnect_error:
                    logger.error(f"❌ Reconnection failed: {reconnect_error}")
                    logger.info("⏳ Waiting 60 seconds before retry...")
                    time.sleep(60)

    def run(self):
        """Main run method"""
        logger.info("⚽ Multi-Club Reddit Transfer Bot Starting...")
        logger.info(f"📋 Monitoring: {', '.join([f'r/{club}' for club in self.clubs.keys()])}")

        # Load seen submissions
        self.load_seen_submissions()

        # Connect to Reddit
        self.connect_to_reddit()

        # Check recent posts for each subreddit (skip Chelsea since it's most active)
        broken_subreddits = ['gunners', 'liverpoolfc', 'mcfc']  # Previously broken due to case mismatch

        for club_key in self.clubs.keys():
            if club_key == 'chelseafc':
                logger.info(f"⏭️ Skipping initial check for r/{club_key} (most active)")
                continue

            # Check more posts for previously broken subreddits
            if club_key in broken_subreddits:
                limit = 5
                logger.info(f"🔍 Checking last {limit} posts from r/{club_key} (was broken, catching up)")
            else:
                limit = 1

            self.check_recent_posts(club_key, limit=limit)
            time.sleep(2)  # Delay between subreddits

        # Save seen submissions after initial check
        self.save_seen_submissions()

        # Start monitoring all subreddits
        try:
            self.monitor_all_subreddits()
        except KeyboardInterrupt:
            logger.info("👋 Bot stopped by user")
        finally:
            self.save_seen_submissions()
            logger.info("💾 Saved seen submissions")


def main():
    """Main function"""
    try:
        bot = MultiClubRedditBot()
        bot.run()
    except Exception as e:
        logger.error(f"❌ Bot failed to start: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())