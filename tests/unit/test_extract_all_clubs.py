#!/usr/bin/env python3
"""
Unit tests for src/extract_all_clubs.py

Tests all major functions including:
- teams_overlap
- categorize_teams
- extract_all_teams
- process_all_players
- find_potential_teammates
"""

import unittest
import json
import os
import sys
import tempfile
from unittest.mock import patch, mock_open, MagicMock
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from cleva.cantonese.soccer.extract_all_clubs import (
    teams_overlap,
    categorize_teams,
    extract_all_teams,
    process_all_players,
    find_potential_teammates,
    analyze_single_player
)


class TestTeamsOverlap(unittest.TestCase):
    """Test the teams_overlap function."""
    
    def test_teams_overlap_with_clear_overlap(self):
        """Test teams with clear overlapping periods."""
        team1 = {
            'start_date': '2015-01-01T00:00:00Z',
            'end_date': '2018-01-01T00:00:00Z'
        }
        team2 = {
            'start_date': '2017-01-01T00:00:00Z',
            'end_date': '2020-01-01T00:00:00Z'
        }
        self.assertTrue(teams_overlap(team1, team2))
    
    def test_teams_overlap_no_overlap(self):
        """Test teams with no overlapping periods."""
        team1 = {
            'start_date': '2015-01-01T00:00:00Z',
            'end_date': '2017-01-01T00:00:00Z'
        }
        team2 = {
            'start_date': '2018-01-01T00:00:00Z',
            'end_date': '2020-01-01T00:00:00Z'
        }
        self.assertFalse(teams_overlap(team1, team2))
    
    def test_teams_overlap_current_team(self):
        """Test overlap with current team (no end date)."""
        team1 = {
            'start_date': '2015-01-01T00:00:00Z',
            'end_date': '2020-01-01T00:00:00Z'
        }
        team2 = {
            'start_date': '2019-01-01T00:00:00Z',
            'end_date': None  # Current team
        }
        self.assertTrue(teams_overlap(team1, team2))
    
    def test_teams_overlap_missing_dates(self):
        """Test teams with missing start dates."""
        team1 = {
            'start_date': None,
            'end_date': '2018-01-01T00:00:00Z'
        }
        team2 = {
            'start_date': '2017-01-01T00:00:00Z',
            'end_date': '2020-01-01T00:00:00Z'
        }
        self.assertFalse(teams_overlap(team1, team2))
    
    def test_teams_overlap_identical_periods(self):
        """Test teams with identical time periods."""
        team1 = {
            'start_date': '2015-01-01T00:00:00Z',
            'end_date': '2018-01-01T00:00:00Z'
        }
        team2 = {
            'start_date': '2015-01-01T00:00:00Z',
            'end_date': '2018-01-01T00:00:00Z'
        }
        self.assertTrue(teams_overlap(team1, team2))


class TestCategorizeTeams(unittest.TestCase):
    """Test the categorize_teams function."""
    
    def test_categorize_teams_mixed(self):
        """Test categorization with mixed team types."""
        all_affiliations = [
            {
                'name': 'Manchester United',
                'description': 'English football club'
            },
            {
                'name': 'England national football team',
                'description': 'National association football team'
            },
            {
                'name': 'England U-21',
                'description': 'Youth national team'
            },
            {
                'name': 'Manchester United Youth',
                'description': 'Youth football team'
            }
        ]
        
        clubs, national_teams, youth_teams = categorize_teams(all_affiliations)
        
        self.assertEqual(len(clubs), 1)
        self.assertEqual(len(national_teams), 1)
        self.assertEqual(len(youth_teams), 2)
        
        # Verify correct categorization
        self.assertEqual(clubs[0]['name'], 'Manchester United')
        self.assertEqual(national_teams[0]['name'], 'England national football team')
        self.assertIn('U-21', youth_teams[0]['name'])
        self.assertIn('Youth', youth_teams[1]['name'])
    
    def test_categorize_teams_clubs_only(self):
        """Test categorization with clubs only."""
        all_affiliations = [
            {
                'name': 'Barcelona',
                'description': 'Spanish football club'
            },
            {
                'name': 'Real Madrid',
                'description': 'Spanish football club'
            }
        ]
        
        clubs, national_teams, youth_teams = categorize_teams(all_affiliations)
        
        self.assertEqual(len(clubs), 2)
        self.assertEqual(len(national_teams), 0)
        self.assertEqual(len(youth_teams), 0)
    
    def test_categorize_teams_empty_input(self):
        """Test categorization with empty input."""
        clubs, national_teams, youth_teams = categorize_teams([])
        
        self.assertEqual(len(clubs), 0)
        self.assertEqual(len(national_teams), 0)
        self.assertEqual(len(youth_teams), 0)


class TestExtractAllTeams(unittest.TestCase):
    """Test the extract_all_teams function."""
    
    def setUp(self):
        """Set up test data."""
        self.mock_jsonld_data = {
            '@graph': [
                {
                    '@id': 'wd:Q107051',
                    '@type': 'wikibase:Item',
                    'label': [
                        {
                            '@language': 'en',
                            '@value': 'Lionel Messi'
                        },
                        {
                            '@language': 'yue',
                            '@value': '美斯'
                        }
                    ]
                },
                {
                    '@type': 'wikibase:Statement',
                    'ps:P54': 'wd:Q5794',
                    'P580': '2004-10-01T00:00:00Z',
                    'P582': '2021-08-01T00:00:00Z'
                },
                {
                    '@type': 'wikibase:Statement',
                    'ps:P54': 'wd:Q10308',
                    'P580': '2021-08-01T00:00:00Z'
                },
                {
                    '@id': 'wd:Q5794',
                    '@type': 'wikibase:Item',
                    'label': [
                        {
                            '@language': 'en',
                            '@value': 'FC Barcelona'
                        },
                        {
                            '@language': 'yue',
                            '@value': '巴塞羅那'
                        }
                    ]
                },
                {
                    '@id': 'wd:Q10308',
                    '@type': 'wikibase:Item',
                    'label': [
                        {
                            '@language': 'en',
                            '@value': 'Paris Saint-Germain'
                        }
                    ]
                }
            ]
        }
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    @patch('cleva.cantonese.soccer.extract_all_clubs.extract_entity_names')
    def test_extract_all_teams_basic(self, mock_extract_names, mock_json_load, mock_file):
        """Test basic team extraction functionality."""
        mock_json_load.return_value = self.mock_jsonld_data
        
        # Mock the extract_entity_names function
        def mock_extract_side_effect(data, entity_id, paranames):
            if entity_id == 'Q107051':
                return {
                    'english': 'Lionel Messi',
                    'cantonese_best': '美斯',
                    'cantonese_lang': 'yue',
                    'cantonese_source': 'wikidata',
                    'description_english': 'Football player'
                }
            elif entity_id == 'Q5794':
                return {
                    'english': 'FC Barcelona',
                    'cantonese_best': '巴塞羅那',
                    'cantonese_lang': 'yue',
                    'cantonese_source': 'wikidata',
                    'description_english': 'Football club'
                }
            elif entity_id == 'Q10308':
                return {
                    'english': 'Paris Saint-Germain',
                    'cantonese_best': 'Unknown',
                    'cantonese_lang': 'none',
                    'cantonese_source': 'none',
                    'description_english': 'Football club'
                }
            return {}
        
        mock_extract_names.side_effect = mock_extract_side_effect
        
        result = extract_all_teams('/fake/path/Q107051.jsonld')
        
        # Verify basic structure
        self.assertEqual(result['player_id'], 'Q107051')
        self.assertEqual(result['player_names']['english'], 'Lionel Messi')
        self.assertEqual(result['player_names']['cantonese_best'], '美斯')
        self.assertTrue(result['has_cantonese_data'])
        
        # Verify team extraction
        self.assertEqual(len(result['all_affiliations']), 2)
        self.assertEqual(len(result['clubs']), 2)  # Both should be categorized as clubs
        self.assertEqual(len(result['former_clubs']), 1)  # Barcelona
        self.assertEqual(len(result['current_clubs']), 1)  # PSG
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_extract_all_teams_invalid_filename(self, mock_json_load, mock_file):
        """Test handling of invalid filename."""
        mock_json_load.return_value = {'@graph': []}
        
        result = extract_all_teams('/fake/path/invalid_file.json')
        
        self.assertIsNone(result['player_id'])
        self.assertEqual(len(result['all_affiliations']), 0)


class TestProcessAllPlayers(unittest.TestCase):
    """Test the process_all_players function."""
    
    @patch('os.listdir')
    @patch('os.path.exists')
    @patch('cleva.cantonese.soccer.extract_all_clubs.extract_all_teams')
    @patch('cleva.cantonese.soccer.extract_all_clubs.load_cached_cantonese_names')
    def test_process_all_players_basic(self, mock_load_cache, mock_extract_teams, mock_exists, mock_listdir):
        """Test basic processing of all players."""
        # Mock file system
        mock_listdir.return_value = ['Q107051.jsonld', 'Q110053.jsonld']
        mock_exists.return_value = False  # No cache
        mock_load_cache.return_value = (None, None)
        
        # Mock extract_all_teams responses
        def mock_extract_side_effect(file_path, cached_players=None, cached_teams=None):
            if 'Q107051' in file_path:
                return {
                    'player_id': 'Q107051',
                    'player_names': {
                        'english': 'Lionel Messi',
                        'cantonese_best': '美斯',
                        'cantonese_lang': 'yue',
                        'cantonese_source': 'wikidata'
                    },
                    'clubs': [
                        {
                            'club_id': 'Q5794',
                            'name': 'FC Barcelona',
                            'cantonese_name': '巴塞羅那',
                            'has_cantonese': True,
                            'club_names': {'cantonese_source': 'wikidata'},
                            'is_current': False,
                            'start_year': 2004,
                            'end_year': 2021
                        }
                    ],
                    'national_teams': [],
                    'has_cantonese_data': True
                }
            elif 'Q110053' in file_path:
                return {
                    'player_id': 'Q110053',
                    'player_names': {
                        'english': 'Test Player',
                        'cantonese_best': 'Unknown',
                        'cantonese_lang': 'none',
                        'cantonese_source': 'none'
                    },
                    'clubs': [],
                    'national_teams': [],
                    'has_cantonese_data': False
                }
        
        mock_extract_teams.side_effect = mock_extract_side_effect
        
        result = process_all_players('/fake/directory')
        
        # Verify structure
        self.assertIn('players', result)
        self.assertIn('club_to_players', result)
        self.assertIn('national_team_to_players', result)
        self.assertIn('cantonese_statistics', result)
        self.assertIn('processing_info', result)
        
        # Verify content
        self.assertEqual(len(result['players']), 2)
        self.assertIn('Q107051', result['players'])
        self.assertIn('Q110053', result['players'])
        
        # Verify statistics
        stats = result['cantonese_statistics']
        self.assertEqual(stats['players_with_cantonese'], 1)
        self.assertEqual(stats['unique_clubs_with_cantonese'], 1)
    
    @patch('os.listdir')
    @patch('cleva.cantonese.soccer.extract_all_clubs.extract_all_teams')
    def test_process_all_players_with_errors(self, mock_extract_teams, mock_listdir):
        """Test processing with errors in some files."""
        mock_listdir.return_value = ['Q107051.jsonld', 'Q110053.jsonld']
        
        # Mock one successful and one failed extraction
        def mock_extract_side_effect(file_path, cached_players=None, cached_teams=None):
            if 'Q107051' in file_path:
                return {
                    'player_id': 'Q107051',
                    'player_names': {
                        'english': 'Lionel Messi',
                        'cantonese_best': '美斯',
                        'cantonese_lang': 'yue',
                        'cantonese_source': 'wikidata'
                    },
                    'clubs': [],
                    'national_teams': [],
                    'has_cantonese_data': True
                }
            else:
                raise Exception("Mock error")
        
        mock_extract_teams.side_effect = mock_extract_side_effect
        
        result = process_all_players('/fake/directory')
        
        # Should process successfully despite errors
        self.assertEqual(len(result['players']), 1)
        self.assertIn('Q107051', result['players'])


class TestFindPotentialTeammates(unittest.TestCase):
    """Test the find_potential_teammates function."""
    
    def test_find_potential_teammates_basic(self):
        """Test basic teammate finding functionality."""
        mock_data = {
            'players': {
                'Q107051': {
                    'player_names': {
                        'english': 'Lionel Messi',
                        'cantonese_best': '美斯',
                        'cantonese_lang': 'yue'
                    },
                    'clubs': [
                        {
                            'club_id': 'Q5794',
                            'name': 'FC Barcelona',
                            'cantonese_name': '巴塞羅那',
                            'has_cantonese': True,
                            'start_year': 2004,
                            'end_year': 2021,
                            'is_current': False
                        }
                    ],
                    'national_teams': []
                },
                'Q110053': {
                    'player_names': {
                        'english': 'Xavi',
                        'cantonese_best': '沙維',
                        'cantonese_lang': 'yue'
                    },
                    'clubs': [
                        {
                            'club_id': 'Q5794',
                            'name': 'FC Barcelona',
                            'cantonese_name': '巴塞羅那',
                            'has_cantonese': True,
                            'start_year': 1998,
                            'end_year': 2015,
                            'is_current': False
                        }
                    ],
                    'national_teams': []
                }
            }
        }
        
        result = find_potential_teammates(mock_data)
        
        # Should find one club teammate pair
        self.assertIn('club_teammates', result)
        self.assertIn('national_teammates', result)
        self.assertEqual(len(result['club_teammates']), 1)
        self.assertEqual(len(result['national_teammates']), 0)
        
        # Verify teammate structure
        teammate_pair = result['club_teammates'][0]
        self.assertIn('player1', teammate_pair)
        self.assertIn('player2', teammate_pair)
        self.assertIn('team', teammate_pair)
        self.assertTrue(teammate_pair['has_any_cantonese'])
    
    def test_find_potential_teammates_no_overlap(self):
        """Test teammate finding with no overlapping periods."""
        mock_data = {
            'players': {
                'Q107051': {
                    'player_names': {
                        'english': 'Lionel Messi',
                        'cantonese_best': '美斯',
                        'cantonese_lang': 'yue'
                    },
                    'clubs': [
                        {
                            'club_id': 'Q5794',
                            'name': 'FC Barcelona',
                            'cantonese_name': '巴塞羅那',
                            'has_cantonese': True,
                            'start_year': 2020,
                            'end_year': 2021,
                            'is_current': False
                        }
                    ],
                    'national_teams': []
                },
                'Q110053': {
                    'player_names': {
                        'english': 'Xavi',
                        'cantonese_best': '沙維',
                        'cantonese_lang': 'yue'
                    },
                    'clubs': [
                        {
                            'club_id': 'Q5794',
                            'name': 'FC Barcelona',
                            'cantonese_name': '巴塞羅那',
                            'has_cantonese': True,
                            'start_year': 1998,
                            'end_year': 2015,
                            'is_current': False
                        }
                    ],
                    'national_teams': []
                }
            }
        }
        
        result = find_potential_teammates(mock_data)
        
        # Should find no teammates due to no overlap
        self.assertEqual(len(result['club_teammates']), 0)
        self.assertEqual(len(result['national_teammates']), 0)


class TestAnalyzeSinglePlayer(unittest.TestCase):
    """Test the analyze_single_player function."""
    
    @patch('cleva.cantonese.soccer.extract_all_clubs.extract_all_teams')
    @patch('builtins.print')
    def test_analyze_single_player_basic(self, mock_print, mock_extract_teams):
        """Test basic single player analysis."""
        mock_extract_teams.return_value = {
            'player_id': 'Q107051',
            'player_names': {
                'english': 'Lionel Messi',
                'cantonese_best': '美斯',
                'cantonese_lang': 'yue',
                'cantonese_source': 'wikidata'
            },
            'clubs': [],
            'national_teams': [],
            'current_clubs': [],
            'former_clubs': [],
            'current_national_teams': [],
            'former_national_teams': [],
            'all_affiliations': [],
            'total_affiliations': 0,
            'has_cantonese_data': True
        }
        
        # Should not raise any exceptions
        analyze_single_player('/fake/path/Q107051.jsonld')
        
        # Verify that print was called (indicating output was generated)
        self.assertTrue(mock_print.called)
    
    @patch('cleva.cantonese.soccer.extract_all_clubs.extract_all_teams')
    @patch('builtins.print')
    def test_analyze_single_player_with_error(self, mock_print, mock_extract_teams):
        """Test single player analysis with error."""
        mock_extract_teams.side_effect = Exception("Mock error")
        
        # Should handle error gracefully
        analyze_single_player('/fake/path/Q107051.jsonld')
        
        # Should print error message
        mock_print.assert_called()


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestTeamsOverlap,
        TestCategorizeTeams,
        TestExtractCantoneseLabels,
        TestExtractAllTeams,
        TestProcessAllPlayers,
        TestFindPotentialTeammates,
        TestAnalyzeSinglePlayer
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
