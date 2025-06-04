#!/usr/bin/env python3
"""
Chelsea Reddit Transfer Bot
Monitors r/chelseafc for Tier 1 and Tier 2 transfer posts and sends to Discord
"""

import praw
import requests
import json
import time
import os
from datetime import datetime
from dotenv import load_dotenv
from typing import Set
import logging


# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ChelseaRedditBot:
    def __init__(self):
        # Reddit API credentials from environment variables
        self.reddit_client_id = os.getenv('REDDIT_CLIENT_ID')
        self.reddit_client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        self.reddit_user_agent = os.getenv('REDDIT_USER_AGENT', 'discord_cfc_bot/1.0')

        # Discord webhook
        self.discord_webhook = os.getenv('DISCORD_WEBHOOK_URL')

        # Validate required environment variables
        if not all([self.reddit_client_id, self.reddit_client_secret, self.discord_webhook]):
            raise ValueError("Missing required environment variables. Check your .env file.")

        # File to store seen submissions
        self.seen_file = 'seen_submissions.json'
        self.seen_submissions: Set[str] = set()

        # Target flairs
        self.target_flairs = ['Tier 1', 'Tier 2']

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

            # Test connection
            test_subreddit = self.reddit.subreddit('chelseafc')
            logger.info(f"✅ Connected to Reddit. r/chelseafc has {test_subreddit.subscribers:,} subscribers")

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
        # Keep only the most recent 1000 to prevent file from growing too large
        if len(seen_list) > 1000:
            seen_list = seen_list[-1000:]
            self.seen_submissions = set(seen_list)

        with open(self.seen_file, 'w') as f:
            json.dump(seen_list, f, indent=2)

    def send_to_discord(self, submission):
        """Send submission to Discord via webhook"""
        # Determine tier and color
        tier = submission.link_flair_text
        color = 0x00FF00 if tier == "Tier 1" else 0xFFFF00  # Green for Tier 1, Yellow for Tier 2

        # Get submission details
        title = submission.title
        url = submission.url
        reddit_url = f"https://reddit.com{submission.permalink}"
        author = str(submission.author) if submission.author else "Unknown"
        created_time = datetime.fromtimestamp(submission.created_utc)

        # Create embed
        embed = {
            "title": f"🔵 {tier} Chelsea Transfer News",
            "description": title,
            "color": color,
            "fields": [
                {
                    "name": "Source",
                    "value": f"[View Article]({url})",
                    "inline": True
                },
                {
                    "name": "Reddit Post",
                    "value": f"[View Discussion]({reddit_url})",
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
                }
            ],
            "timestamp": created_time.isoformat(),
            "footer": {
                "text": "r/chelseafc • Chelsea Transfer Bot"
            },
            "thumbnail": {
                "url": "https://logos-world.net/wp-content/uploads/2020/06/Chelsea-Logo.png"
            }
        }

        payload = {
            "embeds": [embed]
        }

        try:
            response = requests.post(
                self.discord_webhook,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )

            if response.status_code == 204:
                logger.info(f"✅ Posted to Discord: {title[:50]}...")
                return True
            else:
                logger.error(f"❌ Discord webhook failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False

        except requests.RequestException as e:
            logger.error(f"❌ Error posting to Discord: {e}")
            return False

    def process_submission(self, submission):
        """Process a single submission"""
        # Skip if already seen
        if submission.id in self.seen_submissions:
            return False

        # Check if it has the target flair
        if submission.link_flair_text not in self.target_flairs:
            self.seen_submissions.add(submission.id)
            return False

        # Log the submission
        logger.info(f"📢 Found {submission.link_flair_text} post: {submission.title[:50]}...")

        # Send to Discord
        success = self.send_to_discord(submission)

        # Mark as seen regardless of Discord success
        self.seen_submissions.add(submission.id)

        # Save seen submissions periodically
        if len(self.seen_submissions) % 10 == 0:
            self.save_seen_submissions()

        return success

    def check_recent_posts(self, limit=1):
        """Check recent posts for any missed Tier 1/2 posts"""
        logger.info(f"🔍 Checking last 1 posts for missed Tier 1/2 content...")

        subreddit = self.reddit.subreddit('chelseafc')
        found_count = 0

        try:
            for submission in subreddit.new(limit=limit):
                if self.process_submission(submission):
                    found_count += 1
                    time.sleep(2)  # Small delay between Discord posts

            logger.info(f"✅ Initial check complete. Posted {found_count} new items")

        except Exception as e:
            logger.error(f"❌ Error during initial check: {e}")

    def monitor_subreddit(self):
        """Monitor r/chelseafc for new Tier 1/2 posts"""
        logger.info("🚀 Starting live monitoring of r/chelseafc...")

        subreddit = self.reddit.subreddit('chelseafc')

        while True:
            try:
                # Stream new submissions
                for submission in subreddit.stream.submissions(skip_existing=True):
                    self.process_submission(submission)

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
        logger.info("🔵 Chelsea Reddit Transfer Bot Starting...")

        # Load seen submissions
        self.load_seen_submissions()

        # Connect to Reddit
        self.connect_to_reddit()

        # Check recent posts first
        self.check_recent_posts()

        # Save seen submissions after initial check
        self.save_seen_submissions()

        # Start monitoring
        try:
            self.monitor_subreddit()
        except KeyboardInterrupt:
            logger.info("👋 Bot stopped by user")
        finally:
            self.save_seen_submissions()
            logger.info("💾 Saved seen submissions")


def main():
    """Main function"""
    try:
        bot = ChelseaRedditBot()
        bot.run()
    except Exception as e:
        logger.error(f"❌ Bot failed to start: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())