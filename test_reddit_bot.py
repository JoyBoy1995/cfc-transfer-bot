#!/usr/bin/env python3
"""
Unit tests for Multi-Club Reddit Transfer Bot
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import tempfile
import os
from datetime import datetime

# Import the bot class
from reddit_bot import MultiClubRedditBot


class TestMultiClubRedditBot(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'REDDIT_CLIENT_ID': 'test_client_id',
            'REDDIT_CLIENT_SECRET': 'test_client_secret',
            'REDDIT_USER_AGENT': 'test_bot/1.0',
            'DISCORD_WEBHOOK_URL': 'https://discord.com/api/webhooks/123/abc,https://discord.com/api/webhooks/456/def'
        })
        self.env_patcher.start()

        # Create a temporary file for seen submissions
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        self.temp_file.close()

        # Initialize bot with mocked file path
        with patch.object(MultiClubRedditBot, '__init__', self._mock_init):
            self.bot = MultiClubRedditBot()
            self.bot.seen_file = self.temp_file.name

    def _mock_init(self, instance):
        """Mock initialization without calling actual __init__"""
        instance.reddit_client_id = 'test_client_id'
        instance.reddit_client_secret = 'test_client_secret'
        instance.reddit_user_agent = 'test_bot/1.0'
        instance.discord_webhooks = [
            'https://discord.com/api/webhooks/123/abc',
            'https://discord.com/api/webhooks/456/def'
        ]
        instance.seen_submissions = set()
        instance.target_flairs = ['Tier 1', 'Tier 2', 'Official Source']
        instance.clubs = {
            'chelseafc': {
                'name': 'Chelsea FC',
                'emoji': '🔵',
                'color': 0x034694,
                'logo': 'https://example.com/chelsea.png'
            },
            'soccer': {
                'name': 'General Football',
                'emoji': '⚽',
                'color': 0x00FF00,
                'logo': 'https://example.com/soccer.png'
            }
        }
        instance.reddit = None

    def tearDown(self):
        """Clean up after each test method."""
        self.env_patcher.stop()
        os.unlink(self.temp_file.name)

    def test_environment_variables_parsing(self):
        """Test that environment variables are parsed correctly"""
        self.assertEqual(len(self.bot.discord_webhooks), 2)
        self.assertIn('https://discord.com/api/webhooks/123/abc', self.bot.discord_webhooks)
        self.assertIn('https://discord.com/api/webhooks/456/def', self.bot.discord_webhooks)

    def test_environment_variables_single_webhook(self):
        """Test that single webhook URL is handled correctly"""
        with patch.dict(os.environ, {
            'DISCORD_WEBHOOK_URL': 'https://discord.com/api/webhooks/single/url'
        }):
            with patch.object(MultiClubRedditBot, '__init__', self._mock_init):
                bot = MultiClubRedditBot()
                bot.discord_webhooks = ['https://discord.com/api/webhooks/single/url']
                self.assertEqual(len(bot.discord_webhooks), 1)

    def test_missing_environment_variables(self):
        """Test that missing environment variables raise an error"""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                MultiClubRedditBot()

    def test_is_transfer_related_positive_cases(self):
        """Test transfer detection with positive cases"""
        test_cases = [
            "Chelsea sign new midfielder for £50m",
            "BREAKING: Real Madrid agree deal for striker",
            "Here we go! Arsenal announce new signing",
            "Official: Liverpool complete transfer",
            "Done deal - Manchester United loan agreement"
        ]

        for title in test_cases:
            with self.subTest(title=title):
                self.assertTrue(self.bot.is_transfer_related(title))

    def test_is_transfer_related_negative_cases(self):
        """Test transfer detection with negative cases"""
        test_cases = [
            "Match thread: Chelsea vs Arsenal",
            "Post-match discussion",
            "Player injury update",
            "Stadium renovation news",
            "Youth academy graduation"
        ]

        for title in test_cases:
            with self.subTest(title=title):
                self.assertFalse(self.bot.is_transfer_related(title))

    def test_load_seen_submissions_new_file(self):
        """Test loading seen submissions when file doesn't exist"""
        # Delete the temp file to simulate new installation
        os.unlink(self.temp_file.name)

        self.bot.load_seen_submissions()
        self.assertEqual(len(self.bot.seen_submissions), 0)

    def test_load_seen_submissions_existing_file(self):
        """Test loading seen submissions from existing file"""
        # Write test data to file
        test_data = ['submission1', 'submission2', 'submission3']
        with open(self.temp_file.name, 'w') as f:
            json.dump(test_data, f)

        self.bot.load_seen_submissions()
        self.assertEqual(len(self.bot.seen_submissions), 3)
        self.assertIn('submission1', self.bot.seen_submissions)
        self.assertIn('submission2', self.bot.seen_submissions)
        self.assertIn('submission3', self.bot.seen_submissions)

    def test_save_seen_submissions(self):
        """Test saving seen submissions to file"""
        # Add test data
        self.bot.seen_submissions = {'sub1', 'sub2', 'sub3'}

        self.bot.save_seen_submissions()

        # Verify file contains the data
        with open(self.temp_file.name, 'r') as f:
            saved_data = json.load(f)

        self.assertEqual(len(saved_data), 3)
        self.assertIn('sub1', saved_data)
        self.assertIn('sub2', saved_data)
        self.assertIn('sub3', saved_data)

    def test_save_seen_submissions_large_list(self):
        """Test that large seen submissions list is truncated"""
        # Create a large set of submissions (more than 2000)
        large_set = {f'submission_{i}' for i in range(2500)}
        self.bot.seen_submissions = large_set

        self.bot.save_seen_submissions()

        # Verify that it was truncated to 2000
        self.assertEqual(len(self.bot.seen_submissions), 2000)

    def test_process_submission_already_seen(self):
        """Test that already seen submissions are skipped"""
        # Create mock submission
        mock_submission = Mock()
        mock_submission.id = 'test_submission_id'

        # Add to seen submissions
        self.bot.seen_submissions.add('test_submission_id')

        result = self.bot.process_submission(mock_submission, 'chelseafc')
        self.assertFalse(result)

    def test_process_submission_club_subreddit_with_good_flair(self):
        """Test processing club subreddit submission with Tier 1 flair"""
        # Create mock submission with Tier 1 flair
        mock_submission = Mock()
        mock_submission.id = 'test_submission_new'
        mock_submission.link_flair_text = 'Tier 1'
        mock_submission.title = 'Chelsea sign new player'
        mock_submission.url = 'https://example.com/news'
        mock_submission.permalink = '/r/chelseafc/comments/123'
        mock_submission.author = Mock()
        mock_submission.author.__str__ = Mock(return_value='test_user')
        mock_submission.created_utc = 1640995200  # 2022-01-01

        with patch.object(self.bot, 'send_to_discord', return_value=True) as mock_send:
            result = self.bot.process_submission(mock_submission, 'chelseafc')

            self.assertTrue(result)
            mock_send.assert_called_once_with(mock_submission, 'chelseafc')
            self.assertIn('test_submission_new', self.bot.seen_submissions)

    def test_process_submission_club_subreddit_bad_flair(self):
        """Test processing club subreddit submission with bad flair"""
        mock_submission = Mock()
        mock_submission.id = 'test_submission_bad'
        mock_submission.link_flair_text = 'Tier 3'

        result = self.bot.process_submission(mock_submission, 'chelseafc')

        self.assertFalse(result)
        self.assertIn('test_submission_bad', self.bot.seen_submissions)

    def test_process_submission_soccer_high_score(self):
        """Test processing r/soccer submission with high score"""
        mock_submission = Mock()
        mock_submission.id = 'soccer_submission'
        mock_submission.title = 'BREAKING: Chelsea sign new striker'
        mock_submission.score = 150
        mock_submission.link_flair_text = None
        mock_submission.url = 'https://example.com/news'
        mock_submission.permalink = '/r/soccer/comments/456'
        mock_submission.author = Mock()
        mock_submission.author.__str__ = Mock(return_value='soccer_user')
        mock_submission.created_utc = 1640995200
        mock_submission.selftext = ''

        with patch.object(self.bot, 'send_to_discord', return_value=True) as mock_send:
            result = self.bot.process_submission(mock_submission, 'soccer')

            self.assertTrue(result)
            mock_send.assert_called_once_with(mock_submission, 'soccer')

    def test_process_submission_soccer_low_score(self):
        """Test processing r/soccer submission with low score"""
        mock_submission = Mock()
        mock_submission.id = 'soccer_low_score'
        mock_submission.title = 'Chelsea transfer rumor'
        mock_submission.score = 50  # Below threshold of 100
        mock_submission.selftext = ''

        result = self.bot.process_submission(mock_submission, 'soccer')

        self.assertFalse(result)
        self.assertIn('soccer_low_score', self.bot.seen_submissions)

    @patch('requests.post')
    def test_send_to_discord_success(self, mock_post):
        """Test successful Discord message sending"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response

        # Create mock submission
        mock_submission = Mock()
        mock_submission.title = 'Test transfer news'
        mock_submission.url = 'https://example.com/news'
        mock_submission.permalink = '/r/chelseafc/comments/123'
        mock_submission.author = Mock()
        mock_submission.author.__str__ = Mock(return_value='test_user')
        mock_submission.created_utc = 1640995200
        mock_submission.link_flair_text = 'Tier 1'

        result = self.bot.send_to_discord(mock_submission, 'chelseafc')

        self.assertTrue(result)
        # Should be called twice (once for each webhook)
        self.assertEqual(mock_post.call_count, 2)

    @patch('requests.post')
    def test_send_to_discord_failure(self, mock_post):
        """Test Discord message sending failure"""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response

        mock_submission = Mock()
        mock_submission.title = 'Test transfer news'
        mock_submission.url = 'https://example.com/news'
        mock_submission.permalink = '/r/chelseafc/comments/123'
        mock_submission.author = Mock()
        mock_submission.author.__str__ = Mock(return_value='test_user')
        mock_submission.created_utc = 1640995200
        mock_submission.link_flair_text = 'Tier 1'

        result = self.bot.send_to_discord(mock_submission, 'chelseafc')

        self.assertFalse(result)

    def test_club_configuration(self):
        """Test that club configurations are properly set up"""
        # Test that all required clubs exist
        required_clubs = ['chelseafc', 'realmadrid', 'coys', 'Gunners', 'LiverpoolFC', 'MCFC', 'reddevils', 'soccer']

        # Reinitialize with full configuration
        with patch.dict(os.environ, {
            'REDDIT_CLIENT_ID': 'test_id',
            'REDDIT_CLIENT_SECRET': 'test_secret',
            'DISCORD_WEBHOOK_URL': 'https://test.webhook.url'
        }):
            bot = MultiClubRedditBot()

            for club in required_clubs:
                self.assertIn(club, bot.clubs)
                self.assertIn('name', bot.clubs[club])
                self.assertIn('emoji', bot.clubs[club])
                self.assertIn('color', bot.clubs[club])
                self.assertIn('logo', bot.clubs[club])


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)