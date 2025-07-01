#!/usr/bin/env python3
"""
Unit tests for Multi-Club Reddit Transfer Bot
"""

import unittest
from unittest.mock import Mock, patch
import json
import tempfile
import os

# We need to mock the environment before importing the bot
os.environ['REDDIT_CLIENT_ID'] = 'test_client_id'
os.environ['REDDIT_CLIENT_SECRET'] = 'test_client_secret'
os.environ['REDDIT_USER_AGENT'] = 'test_bot/1.0'
os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/123/abc,https://discord.com/api/webhooks/456/def'

# Import the bot class after setting environment
from reddit_bot import MultiClubRedditBot


class TestMultiClubRedditBot(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a temporary file for seen submissions
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        self.temp_file.close()

        # Initialize bot
        self.bot = MultiClubRedditBot()
        self.bot.seen_file = self.temp_file.name
        self.bot.seen_submissions = set()

    def tearDown(self):
        """Clean up after each test method."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_webhook_parsing_multiple(self):
        """Test parsing multiple webhook URLs"""
        self.assertEqual(len(self.bot.discord_webhooks), 2)
        self.assertIn('https://discord.com/api/webhooks/123/abc', self.bot.discord_webhooks)
        self.assertIn('https://discord.com/api/webhooks/456/def', self.bot.discord_webhooks)

    def test_webhook_parsing_single(self):
        """Test parsing single webhook URL"""
        with patch.dict(os.environ, {'DISCORD_WEBHOOK_URL': 'https://single.webhook.url'}):
            bot = MultiClubRedditBot()
            self.assertEqual(len(bot.discord_webhooks), 1)
            self.assertEqual(bot.discord_webhooks[0], 'https://single.webhook.url')

    def test_webhook_parsing_with_spaces(self):
        """Test parsing webhooks with extra spaces"""
        with patch.dict(os.environ, {'DISCORD_WEBHOOK_URL': ' https://url1.com , , https://url2.com '}):
            bot = MultiClubRedditBot()
            self.assertEqual(len(bot.discord_webhooks), 2)
            self.assertIn('https://url1.com', bot.discord_webhooks)
            self.assertIn('https://url2.com', bot.discord_webhooks)

    def test_missing_credentials_raises_error(self):
        """Test that missing credentials raise ValueError"""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                MultiClubRedditBot()

    def test_transfer_detection_positive(self):
        """Test transfer keyword detection - positive cases"""
        positive_cases = [
            "Chelsea signs new striker for £50m",
            "BREAKING: Real Madrid complete transfer deal",
            "Here we go! Arsenal announce new signing",
            "Official: Liverpool player joins Manchester United",
            "Done deal - Tottenham loan agreement confirmed"
        ]

        for case in positive_cases:
            with self.subTest(case=case):
                self.assertTrue(self.bot.is_transfer_related(case))

    def test_transfer_detection_negative(self):
        """Test transfer keyword detection - negative cases"""
        negative_cases = [
            "Match thread: Chelsea vs Arsenal",
            "Post-match discussion and analysis",
            "Player injury update from training",
            "Stadium renovation progress update",
            "Youth team graduation ceremony"
        ]

        for case in negative_cases:
            with self.subTest(case=case):
                self.assertFalse(self.bot.is_transfer_related(case))

    def test_load_submissions_empty_file(self):
        """Test loading when no file exists"""
        # Remove the file to simulate first run
        os.unlink(self.temp_file.name)

        self.bot.load_seen_submissions()
        self.assertEqual(len(self.bot.seen_submissions), 0)

    def test_load_submissions_with_data(self):
        """Test loading existing submissions"""
        test_data = ['sub1', 'sub2', 'sub3']
        with open(self.temp_file.name, 'w') as f:
            json.dump(test_data, f)

        self.bot.load_seen_submissions()
        self.assertEqual(len(self.bot.seen_submissions), 3)
        for item in test_data:
            self.assertIn(item, self.bot.seen_submissions)

    def test_save_submissions(self):
        """Test saving submissions to file"""
        test_data = {'sub1', 'sub2', 'sub3'}
        self.bot.seen_submissions = test_data

        self.bot.save_seen_submissions()

        # Verify data was saved
        with open(self.temp_file.name, 'r') as f:
            saved_data = json.load(f)

        self.assertEqual(len(saved_data), 3)
        for item in test_data:
            self.assertIn(item, saved_data)

    def test_save_submissions_truncation(self):
        """Test that large submission lists are truncated"""
        # Create more than 2000 submissions
        large_set = {f'sub_{i}' for i in range(2500)}
        self.bot.seen_submissions = large_set

        self.bot.save_seen_submissions()

        # Should be truncated to 2000
        self.assertEqual(len(self.bot.seen_submissions), 2000)

    def test_process_already_seen(self):
        """Test processing already seen submission"""
        mock_sub = Mock()
        mock_sub.id = 'seen_before'

        # Mark as already seen
        self.bot.seen_submissions.add('seen_before')

        result = self.bot.process_submission(mock_sub, 'chelseafc')
        self.assertFalse(result)

    def test_process_good_flair(self):
        """Test processing submission with good flair"""
        mock_sub = Mock()
        mock_sub.id = 'new_sub'
        mock_sub.link_flair_text = 'Tier 1'
        mock_sub.title = 'Chelsea signs new player'

        # Mock the Discord sending
        with patch.object(self.bot, 'send_to_discord', return_value=True):
            result = self.bot.process_submission(mock_sub, 'chelseafc')

            self.assertTrue(result)
            self.assertIn('new_sub', self.bot.seen_submissions)

    def test_process_bad_flair(self):
        """Test processing submission with bad flair"""
        mock_sub = Mock()
        mock_sub.id = 'bad_flair_sub'
        mock_sub.link_flair_text = 'Tier 3'

        result = self.bot.process_submission(mock_sub, 'chelseafc')

        self.assertFalse(result)
        self.assertIn('bad_flair_sub', self.bot.seen_submissions)

    def test_process_soccer_high_score(self):
        """Test processing r/soccer with high score"""
        mock_sub = Mock()
        mock_sub.id = 'soccer_sub'
        mock_sub.title = 'BREAKING: Chelsea transfer news'
        mock_sub.score = 150
        mock_sub.link_flair_text = None
        mock_sub.selftext = ''

        with patch.object(self.bot, 'send_to_discord', return_value=True):
            result = self.bot.process_submission(mock_sub, 'soccer')
            self.assertTrue(result)

    def test_process_soccer_low_score(self):
        """Test processing r/soccer with low score"""
        mock_sub = Mock()
        mock_sub.id = 'low_score_sub'
        mock_sub.title = 'Chelsea transfer rumor'
        mock_sub.score = 50
        mock_sub.selftext = ''

        result = self.bot.process_submission(mock_sub, 'soccer')

        self.assertFalse(result)
        self.assertIn('low_score_sub', self.bot.seen_submissions)

    @patch('requests.post')
    def test_discord_send_success(self, mock_post):
        """Test successful Discord sending"""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response

        mock_sub = Mock()
        mock_sub.title = 'Test news'
        mock_sub.url = 'https://test.com'
        mock_sub.permalink = '/r/test/123'
        mock_sub.author = Mock()
        mock_sub.author.__str__ = Mock(return_value='testuser')
        mock_sub.created_utc = 1640995200
        mock_sub.link_flair_text = 'Tier 1'

        result = self.bot.send_to_discord(mock_sub, 'chelseafc')

        self.assertTrue(result)
        # Should be called twice (2 webhooks)
        self.assertEqual(mock_post.call_count, 2)

    @patch('requests.post')
    def test_discord_send_partial_failure(self, mock_post):
        """Test partial Discord sending failure"""
        # First succeeds, second fails
        responses = [Mock(), Mock()]
        responses[0].status_code = 204
        responses[1].status_code = 400
        mock_post.side_effect = responses

        mock_sub = Mock()
        mock_sub.title = 'Test news'
        mock_sub.url = 'https://test.com'
        mock_sub.permalink = '/r/test/123'
        mock_sub.author = Mock()
        mock_sub.author.__str__ = Mock(return_value='testuser')
        mock_sub.created_utc = 1640995200
        mock_sub.link_flair_text = 'Tier 1'

        result = self.bot.send_to_discord(mock_sub, 'chelseafc')

        # Should return True if at least one succeeds
        self.assertTrue(result)
        self.assertEqual(mock_post.call_count, 2)

    @patch('requests.post')
    def test_discord_send_all_fail(self, mock_post):
        """Test all Discord webhooks failing"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response

        mock_sub = Mock()
        mock_sub.title = 'Test news'
        mock_sub.url = 'https://test.com'
        mock_sub.permalink = '/r/test/123'
        mock_sub.author = Mock()
        mock_sub.author.__str__ = Mock(return_value='testuser')
        mock_sub.created_utc = 1640995200
        mock_sub.link_flair_text = 'Tier 1'

        result = self.bot.send_to_discord(mock_sub, 'chelseafc')

        # Should return False if all fail
        self.assertFalse(result)
        self.assertEqual(mock_post.call_count, 2)

    def test_club_configurations(self):
        """Test that all clubs are properly configured"""
        expected_clubs = [
            'chelseafc', 'realmadrid', 'coys', 'Gunners',
            'LiverpoolFC', 'MCFC', 'reddevils', 'soccer'
        ]

        for club in expected_clubs:
            self.assertIn(club, self.bot.clubs)
            club_config = self.bot.clubs[club]

            # Check required fields
            self.assertIn('name', club_config)
            self.assertIn('emoji', club_config)
            self.assertIn('color', club_config)
            self.assertIn('logo', club_config)

            # Check types
            self.assertIsInstance(club_config['name'], str)
            self.assertIsInstance(club_config['emoji'], str)
            self.assertIsInstance(club_config['color'], int)
            self.assertIsInstance(club_config['logo'], str)

    def test_target_flairs(self):
        """Test that target flairs are correctly set"""
        expected_flairs = ['Tier 1', 'Tier 2', 'Official Source']
        self.assertEqual(self.bot.target_flairs, expected_flairs)


if __name__ == '__main__':
    unittest.main(verbosity=2)