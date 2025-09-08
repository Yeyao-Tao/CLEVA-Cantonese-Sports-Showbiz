#!/usr/bin/env python3
"""
Unit tests for src/extract_cantonese_names.py

Tests all major functions including:
- extract_all_entity_ids_from_jsonld
- extract_all_cantonese_names
- save_cantonese_mappings
"""

import unittest
import json
import os
import sys
import tempfile
import shutil
from unittest.mock import patch, mock_open, MagicMock, call
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from extract_cantonese_names import (
    extract_all_entity_ids_from_jsonld,
    extract_all_cantonese_names,
    save_cantonese_mappings
)


class TestExtractAllEntityIdsFromJsonld(unittest.TestCase):
    """Test the extract_all_entity_ids_from_jsonld function."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_player_id = "Q107051"
        self.test_team_id = "Q9616"
        self.test_file_path = f"/test/path/{self.test_player_id}.jsonld"
        
        # Sample WikiData JSONLD structure with player and team data
        self.sample_jsonld_data = {
            '@graph': [
                {
                    '@id': f'wd:{self.test_player_id}',
                    '@type': 'wikibase:Item',
                    'rdfs:label': [
                        {
                            '@language': 'en',
                            '@value': 'Test Player'
                        }
                    ]
                },
                {
                    '@type': ['wikibase:Statement'],
                    'ps:P54': f'wd:{self.test_team_id}',
                    'wikibase:rank': 'wikibase:NormalRank'
                },
                {
                    '@type': 'wikibase:Statement',
                    'ps:P54': f'wd:{self.test_team_id}',
                    'wikibase:rank': 'wikibase:PreferredRank'
                }
            ]
        }
    
    @patch('extract_cantonese_names.load_jsonld_file')
    @patch('extract_cantonese_names.extract_player_id_from_filename')
    def test_extract_entity_ids_success(self, mock_extract_id, mock_load_jsonld):
        """Test successful extraction of entity IDs."""
        mock_extract_id.return_value = self.test_player_id
        mock_load_jsonld.return_value = self.sample_jsonld_data
        
        result = extract_all_entity_ids_from_jsonld(self.test_file_path)
        
        expected_ids = {self.test_player_id, self.test_team_id}
        self.assertEqual(result, expected_ids)
        mock_load_jsonld.assert_called_once_with(self.test_file_path)
        mock_extract_id.assert_called_once_with(self.test_file_path)
    
    @patch('extract_cantonese_names.load_jsonld_file')
    @patch('extract_cantonese_names.extract_player_id_from_filename')
    def test_extract_entity_ids_no_player_id(self, mock_extract_id, mock_load_jsonld):
        """Test extraction when player ID cannot be extracted from filename."""
        mock_extract_id.return_value = None
        mock_load_jsonld.return_value = self.sample_jsonld_data
        
        result = extract_all_entity_ids_from_jsonld(self.test_file_path)
        
        # Should only contain team ID, not player ID
        expected_ids = {self.test_team_id}
        self.assertEqual(result, expected_ids)
    
    @patch('extract_cantonese_names.load_jsonld_file')
    @patch('extract_cantonese_names.extract_player_id_from_filename')
    def test_extract_entity_ids_no_teams(self, mock_extract_id, mock_load_jsonld):
        """Test extraction when no team data is present."""
        mock_extract_id.return_value = self.test_player_id
        jsonld_data_no_teams = {
            '@graph': [
                {
                    '@id': f'wd:{self.test_player_id}',
                    '@type': 'wikibase:Item',
                    'rdfs:label': [
                        {
                            '@language': 'en',
                            '@value': 'Test Player'
                        }
                    ]
                }
            ]
        }
        mock_load_jsonld.return_value = jsonld_data_no_teams
        
        result = extract_all_entity_ids_from_jsonld(self.test_file_path)
        
        # Should only contain player ID
        expected_ids = {self.test_player_id}
        self.assertEqual(result, expected_ids)
    
    @patch('extract_cantonese_names.load_jsonld_file')
    def test_extract_entity_ids_load_error(self, mock_load_jsonld):
        """Test handling of file loading errors."""
        mock_load_jsonld.side_effect = Exception("File not found")
        
        result = extract_all_entity_ids_from_jsonld(self.test_file_path)
        
        # Should return empty set on error
        self.assertEqual(result, set())
    
    @patch('extract_cantonese_names.load_jsonld_file')
    @patch('extract_cantonese_names.extract_player_id_from_filename')
    def test_extract_entity_ids_multiple_types(self, mock_extract_id, mock_load_jsonld):
        """Test extraction with different @type formats (list vs string)."""
        mock_extract_id.return_value = self.test_player_id
        # Test with @type as string instead of list
        jsonld_data_string_type = {
            '@graph': [
                {
                    '@id': f'wd:{self.test_player_id}',
                    '@type': 'wikibase:Item'
                },
                {
                    '@type': 'wikibase:Statement',
                    'ps:P54': f'wd:{self.test_team_id}'
                }
            ]
        }
        mock_load_jsonld.return_value = jsonld_data_string_type
        
        result = extract_all_entity_ids_from_jsonld(self.test_file_path)
        
        expected_ids = {self.test_player_id, self.test_team_id}
        self.assertEqual(result, expected_ids)


class TestExtractAllCantoneseNames(unittest.TestCase):
    """Test the extract_all_cantonese_names function."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_directory = "/test/directory"
        self.test_paranames_path = "/test/paranames.tsv"
        self.test_player_id = "Q107051"
        self.test_team_id = "Q9616"
        self.test_file_path = f"{self.test_directory}/{self.test_player_id}.jsonld"
        
        # Mock entity names data
        self.mock_player_names = {
            'id': self.test_player_id,
            'english': 'Test Player',
            'cantonese': {'yue': '測試球員'},
            'cantonese_best': '測試球員',
            'cantonese_lang': 'yue',
            'description_english': 'Test player description',
            'description_cantonese': {},
            'cantonese_source': 'wikidata'
        }
        
        self.mock_team_names = {
            'id': self.test_team_id,
            'english': 'Test Team',
            'cantonese': {'zh-hk': '測試球隊'},
            'cantonese_best': '測試球隊',
            'cantonese_lang': 'zh-hk',
            'description_english': 'Test team description',
            'description_cantonese': {},
            'cantonese_source': 'paranames'
        }
    
    @patch('extract_cantonese_names.get_all_jsonld_files')
    def test_extract_no_files_found(self, mock_get_files):
        """Test handling when no JSONLD files are found."""
        mock_get_files.return_value = []
        
        result = extract_all_cantonese_names(self.test_directory)
        
        self.assertIn('error', result)
        self.assertEqual(result['players'], {})
        self.assertEqual(result['teams'], {})
        mock_get_files.assert_called_once_with(self.test_directory)
    
    @patch('extract_cantonese_names.load_paranames_cantonese')
    @patch('extract_cantonese_names.get_all_jsonld_files')
    @patch('extract_cantonese_names.extract_all_entity_ids_from_jsonld')
    @patch('extract_cantonese_names.extract_player_id_from_filename')
    @patch('extract_cantonese_names.load_jsonld_file')
    @patch('extract_cantonese_names.extract_entity_names')
    def test_extract_cantonese_names_success(self, mock_extract_names, mock_load_jsonld, 
                                           mock_extract_id, mock_extract_entity_ids, 
                                           mock_get_files, mock_load_paranames):
        """Test successful extraction of Cantonese names."""
        # Setup mocks
        mock_load_paranames.return_value = {'Q107051': 'paranames_data'}
        mock_get_files.return_value = [self.test_file_path]
        mock_extract_entity_ids.return_value = {self.test_player_id, self.test_team_id}
        mock_extract_id.return_value = self.test_player_id
        mock_load_jsonld.return_value = {'@graph': []}
        
        # Mock extract_entity_names to return different data for player vs team
        def mock_extract_names_side_effect(data, entity_id, paranames):
            if entity_id == self.test_player_id:
                return self.mock_player_names
            elif entity_id == self.test_team_id:
                return self.mock_team_names
            else:
                return {
                    'id': entity_id,
                    'english': 'Unknown',
                    'cantonese': {},
                    'cantonese_best': 'Unknown',
                    'cantonese_lang': 'none',
                    'description_english': '',
                    'description_cantonese': {},
                    'cantonese_source': 'none'
                }
        
        mock_extract_names.side_effect = mock_extract_names_side_effect
        
        result = extract_all_cantonese_names(self.test_directory, self.test_paranames_path)
        
        # Verify results
        self.assertNotIn('error', result)
        self.assertEqual(len(result['players']), 1)
        self.assertEqual(len(result['teams']), 1)
        self.assertEqual(result['players'][self.test_player_id], self.mock_player_names)
        self.assertEqual(result['teams'][self.test_team_id], self.mock_team_names)
        
        # Verify statistics
        stats = result['statistics']
        self.assertEqual(stats['total_players'], 1)
        self.assertEqual(stats['total_teams'], 1)
        self.assertEqual(stats['players_with_cantonese'], 1)
        self.assertEqual(stats['teams_with_cantonese'], 1)
        self.assertEqual(stats['players_cantonese_percentage'], 100.0)
        self.assertEqual(stats['teams_cantonese_percentage'], 100.0)
        self.assertEqual(stats['players_from_wikidata'], 1)
        self.assertEqual(stats['players_from_paranames'], 0)
        self.assertEqual(stats['teams_from_wikidata'], 0)
        self.assertEqual(stats['teams_from_paranames'], 1)
        
        # Verify processing info
        processing_info = result['processing_info']
        self.assertEqual(processing_info['directory_processed'], self.test_directory)
        self.assertEqual(processing_info['paranames_file_used'], self.test_paranames_path)
        self.assertEqual(processing_info['jsonld_files_processed'], 1)
    
    @patch('extract_cantonese_names.get_all_jsonld_files')
    @patch('extract_cantonese_names.extract_all_entity_ids_from_jsonld')
    @patch('extract_cantonese_names.extract_player_id_from_filename')
    @patch('extract_cantonese_names.load_jsonld_file')
    def test_extract_cantonese_names_file_error(self, mock_load_jsonld, mock_extract_id, 
                                              mock_extract_entity_ids, mock_get_files):
        """Test handling of file processing errors."""
        mock_get_files.return_value = [self.test_file_path]
        mock_extract_entity_ids.return_value = {self.test_player_id}
        mock_extract_id.return_value = self.test_player_id
        mock_load_jsonld.side_effect = Exception("File corrupted")
        
        result = extract_all_cantonese_names(self.test_directory)
        
        # Should still return valid structure even with errors
        self.assertNotIn('error', result)
        # Function creates minimal entries for missing entities, so player will be present
        self.assertEqual(len(result['players']), 1)
        # Player should have minimal/unknown data due to error
        player_data = result['players'][self.test_player_id]
        self.assertEqual(player_data['english'], 'Unknown')
        self.assertEqual(player_data['cantonese_lang'], 'none')
        self.assertEqual(len(result['teams']), 0)
    
    @patch('extract_cantonese_names.get_all_jsonld_files')
    @patch('extract_cantonese_names.extract_all_entity_ids_from_jsonld')
    @patch('extract_cantonese_names.extract_player_id_from_filename')
    @patch('extract_cantonese_names.load_jsonld_file')
    @patch('extract_cantonese_names.extract_entity_names')
    def test_extract_cantonese_names_no_paranames(self, mock_extract_names, mock_load_jsonld,
                                                 mock_extract_id, mock_extract_entity_ids, 
                                                 mock_get_files):
        """Test extraction without ParaNames file."""
        mock_get_files.return_value = [self.test_file_path]
        mock_extract_entity_ids.return_value = {self.test_player_id}
        mock_extract_id.return_value = self.test_player_id
        mock_load_jsonld.return_value = {'@graph': []}
        mock_extract_names.return_value = self.mock_player_names
        
        result = extract_all_cantonese_names(self.test_directory)  # No paranames_tsv_path
        
        # Should work without paranames
        self.assertNotIn('error', result)
        self.assertEqual(len(result['players']), 1)
        self.assertIsNone(result['processing_info']['paranames_file_used'])


class TestSaveCantoneseMapping(unittest.TestCase):
    """Test the save_cantonese_mappings function."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_data = {
            'players': {
                'Q107051': {
                    'id': 'Q107051',
                    'english': 'Test Player',
                    'cantonese': {'yue': '測試球員'},
                    'cantonese_best': '測試球員',
                    'cantonese_lang': 'yue',
                    'description_english': 'Test player',
                    'description_cantonese': {},
                    'cantonese_source': 'wikidata'
                }
            },
            'teams': {
                'Q9616': {
                    'id': 'Q9616',
                    'english': 'Test Team',
                    'cantonese': {'zh-hk': '測試球隊'},
                    'cantonese_best': '測試球隊',
                    'cantonese_lang': 'zh-hk',
                    'description_english': 'Test team',
                    'description_cantonese': {},
                    'cantonese_source': 'paranames'
                }
            },
            'statistics': {
                'total_players': 1,
                'total_teams': 1,
                'players_with_cantonese': 1,
                'teams_with_cantonese': 1,
                'players_cantonese_percentage': 100.0,
                'teams_cantonese_percentage': 100.0,
                'players_from_wikidata': 1,
                'players_from_paranames': 0,
                'teams_from_wikidata': 0,
                'teams_from_paranames': 1
            },
            'processing_info': {
                'timestamp': '2024-01-01T12:00:00',
                'directory_processed': '/test/dir',
                'paranames_file_used': '/test/paranames.tsv',
                'jsonld_files_processed': 1
            }
        }
    
    def test_save_cantonese_mappings_success(self):
        """Test successful saving of Cantonese mappings."""
        with tempfile.TemporaryDirectory() as temp_dir:
            player_file, team_file, stats_file = save_cantonese_mappings(self.test_data, temp_dir)
            
            # Verify files were created
            self.assertTrue(os.path.exists(player_file))
            self.assertTrue(os.path.exists(team_file))
            self.assertTrue(os.path.exists(stats_file))
            
            # Verify file names
            self.assertEqual(os.path.basename(player_file), 'players_cantonese_names.json')
            self.assertEqual(os.path.basename(team_file), 'teams_cantonese_names.json')
            self.assertEqual(os.path.basename(stats_file), 'cantonese_extraction_stats.json')
            
            # Verify player file content
            with open(player_file, 'r', encoding='utf-8') as f:
                player_data = json.load(f)
            
            self.assertIn('metadata', player_data)
            self.assertIn('players', player_data)
            self.assertEqual(player_data['metadata']['total_players'], 1)
            self.assertEqual(player_data['metadata']['players_with_cantonese'], 1)
            self.assertEqual(player_data['metadata']['cantonese_coverage_percentage'], 100.0)
            self.assertEqual(player_data['players']['Q107051']['english'], 'Test Player')
            
            # Verify team file content
            with open(team_file, 'r', encoding='utf-8') as f:
                team_data = json.load(f)
            
            self.assertIn('metadata', team_data)
            self.assertIn('teams', team_data)
            self.assertEqual(team_data['metadata']['total_teams'], 1)
            self.assertEqual(team_data['metadata']['teams_with_cantonese'], 1)
            self.assertEqual(team_data['teams']['Q9616']['english'], 'Test Team')
            
            # Verify stats file content
            with open(stats_file, 'r', encoding='utf-8') as f:
                stats_data = json.load(f)
            
            self.assertIn('metadata', stats_data)
            self.assertIn('statistics', stats_data)
            self.assertIn('processing_info', stats_data)
            self.assertEqual(stats_data['statistics']['total_players'], 1)
            self.assertEqual(stats_data['statistics']['total_teams'], 1)
    
    def test_save_cantonese_mappings_creates_directory(self):
        """Test that save_cantonese_mappings creates output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            non_existent_dir = os.path.join(temp_dir, 'new_output_dir')
            
            # Directory should not exist initially
            self.assertFalse(os.path.exists(non_existent_dir))
            
            # Function should create the directory
            player_file, team_file, stats_file = save_cantonese_mappings(self.test_data, non_existent_dir)
            
            # Directory should now exist
            self.assertTrue(os.path.exists(non_existent_dir))
            
            # Files should be created
            self.assertTrue(os.path.exists(player_file))
            self.assertTrue(os.path.exists(team_file))
            self.assertTrue(os.path.exists(stats_file))
    
    def test_save_cantonese_mappings_without_paranames(self):
        """Test saving when no ParaNames file was used."""
        # Modify test data to not include ParaNames
        test_data_no_paranames = self.test_data.copy()
        test_data_no_paranames['processing_info']['paranames_file_used'] = None
        
        with tempfile.TemporaryDirectory() as temp_dir:
            player_file, team_file, stats_file = save_cantonese_mappings(test_data_no_paranames, temp_dir)
            
            # Verify player file metadata reflects no ParaNames usage
            with open(player_file, 'r', encoding='utf-8') as f:
                player_data = json.load(f)
            
            expected_sources = ['WikiData JSONLD']
            self.assertEqual(player_data['metadata']['sources'], expected_sources)
            
            # Verify team file metadata reflects no ParaNames usage
            with open(team_file, 'r', encoding='utf-8') as f:
                team_data = json.load(f)
            
            self.assertEqual(team_data['metadata']['sources'], expected_sources)


if __name__ == '__main__':
    unittest.main()
