#!/usr/bin/env python3
"""
Script to extract jersey numbers for football players from WikiData JSONLD files.

This script reads the player jsonld files and extracts jersey number information,
including the number, associated team(s), and time periods when the number was used.

Outputs structured data for all players to support Cantonese benchmark construction.
"""

import json
import os
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add the current directory to Python path to import utils
sys.path.append(os.path.dirname(__file__))

from utils.jsonld_reader import (
    extract_entity_names,
    load_jsonld_file
)
from utils.cantonese_utils import (
    load_cached_cantonese_names,
    get_entity_names_from_cache
)
from utils.date_utils import parse_date
from utils.file_utils import extract_player_id_from_filename


def extract_jersey_numbers(jsonld_file_path: str, cached_players: Dict = None, cached_teams: Dict = None) -> Dict[str, Any]:
    """
    Extract jersey number information for a football player from WikiData JSONLD.
    
    Args:
        jsonld_file_path: Path to the JSONLD file containing player data
        cached_players: Dictionary of cached player names
        cached_teams: Dictionary of cached team names
        
    Returns:
        Dictionary containing player and jersey number information
    """
    with open(jsonld_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    result = {
        'player_id': None,
        'player_names': {},  # Will contain English and Cantonese names
        'jersey_numbers': [],  # List of jersey number entries
        'total_jersey_numbers': 0,
        'teams_with_numbers': [],  # List of unique teams where player had jersey numbers
        'file_path': jsonld_file_path,
        'has_cantonese_data': False,  # Track if player has Cantonese names
        'has_jersey_data': False  # Track if player has any jersey number data
    }
    
    # Extract player ID from filename
    filename = os.path.basename(jsonld_file_path)
    if filename.startswith('Q') and filename.endswith('.jsonld'):
        player_id = filename[:-7]  # Remove .jsonld extension
        result['player_id'] = player_id
        
        # Get player names from cache if available, otherwise use fallback
        if cached_players:
            cached_names = get_entity_names_from_cache(player_id, cached_players)
            if cached_names:
                result['player_names'] = cached_names
            else:
                # Fallback to dynamic extraction if not in cache
                result['player_names'] = extract_entity_names(data, player_id, None)
        else:
            # No cache available, use dynamic extraction
            result['player_names'] = extract_entity_names(data, player_id, None)
        
        # Check if we have Cantonese data for the player
        if result['player_names']['cantonese_lang'] != 'none':
            result['has_cantonese_data'] = True
    
    # Extract jersey number information from detailed statements
    jersey_statements = []
    for item in data.get('@graph', []):
        # Look for P1618 (jersey number) statements
        item_type = item.get('@type')
        is_statement = False
        
        if isinstance(item_type, list):
            is_statement = 'wikibase:Statement' in item_type
        elif isinstance(item_type, str):
            is_statement = item_type == 'wikibase:Statement'
        
        if is_statement and 'ps:P1618' in item:
            jersey_number = item.get('ps:P1618', '')
            start_date = item.get('P580')  # start time
            end_date = item.get('P582')    # end time
            teams = item.get('pq:P54', [])  # team qualifier(s)
            
            # Ensure teams is a list
            if isinstance(teams, str):
                teams = [teams]
            elif not isinstance(teams, list):
                teams = []
            
            # Clean team IDs (remove 'wd:' prefix if present)
            clean_teams = []
            for team in teams:
                if isinstance(team, str):
                    clean_team_id = team.replace('wd:', '')
                    clean_teams.append(clean_team_id)
            
            # Check if this is a current jersey number (no end date)
            is_current = (end_date is None or 
                         (isinstance(end_date, dict) and end_date.get('@id', '').startswith('_:')))
            
            jersey_info = {
                'number': jersey_number,
                'start_date': start_date,
                'end_date': end_date,
                'start_year': parse_date(start_date),
                'end_year': parse_date(end_date),
                'is_current': is_current,
                'teams': clean_teams,  # List of team IDs where this number was used
                'team_details': []  # Will contain team names and details
            }
            
            jersey_statements.append(jersey_info)
    
    # Extract team names and descriptions for each jersey number entry
    teams_with_numbers = set()
    for jersey_info in jersey_statements:
        for team_id in jersey_info['teams']:
            if team_id:
                teams_with_numbers.add(team_id)
                
                # Get team names from cache if available, otherwise use fallback
                if cached_teams:
                    cached_names = get_entity_names_from_cache(team_id, None, cached_teams)
                    if cached_names:
                        team_names = cached_names
                    else:
                        # Fallback to dynamic extraction if not in cache
                        team_names = extract_entity_names(data, team_id, None)
                else:
                    # No cache available, use dynamic extraction
                    team_names = extract_entity_names(data, team_id, None)
                
                team_detail = {
                    'team_id': team_id,
                    'team_names': team_names,
                    'name': team_names['english'],
                    'cantonese_name': team_names['cantonese_best'],
                    'has_cantonese': team_names['cantonese_lang'] != 'none'
                }
                
                jersey_info['team_details'].append(team_detail)
                
                # Track if any team has Cantonese data
                if team_detail['has_cantonese']:
                    result['has_cantonese_data'] = True
    
    result['jersey_numbers'] = jersey_statements
    result['total_jersey_numbers'] = len(jersey_statements)
    result['teams_with_numbers'] = list(teams_with_numbers)
    result['has_jersey_data'] = len(jersey_statements) > 0
    
    return result


def process_all_players_jersey_numbers(directory_path: str, cache_dir: str = None) -> Dict[str, Any]:
    """Process all player files and extract jersey number data using cached Cantonese names for improved performance."""
    
    # Load cached Cantonese names if available
    cached_players = None
    cached_teams = None
    cache_info = "No cache used"
    
    if cache_dir and os.path.exists(cache_dir):
        print(f"Loading cached Cantonese names from {cache_dir}...")
        cached_players, cached_teams = load_cached_cantonese_names(cache_dir)
        if cached_players and cached_teams:
            cache_info = f"Using cached names for {len(cached_players)} players and {len(cached_teams)} teams"
            print(cache_info)
        else:
            print("Failed to load cached names, proceeding without cache")
    else:
        print("No cache directory provided or cache directory not found, proceeding without cache")
    
    all_players = {}
    jersey_number_stats = {
        'players_with_jersey_numbers': 0,
        'players_with_cantonese': 0,
        'players_with_both': 0,
        'total_jersey_entries': 0,
        'unique_teams_with_jersey_data': set(),
        'teams_with_cantonese_names': set(),
        'jersey_numbers_by_team': {},  # team_id -> list of jersey number entries
        'cache_info': cache_info
    }
    
    files = [f for f in os.listdir(directory_path) if f.endswith('.jsonld')]
    
    print(f"Processing {len(files)} player files for jersey number extraction...")
    
    for i, filename in enumerate(files, 1):
        if i % 10 == 0:
            print(f"Processed {i}/{len(files)} files...")
            
        file_path = os.path.join(directory_path, filename)
        
        try:
            player_data = extract_jersey_numbers(file_path, cached_players, cached_teams)
            player_id = player_data['player_id']
            
            if player_id:
                all_players[player_id] = player_data
                
                # Track statistics
                if player_data['has_jersey_data']:
                    jersey_number_stats['players_with_jersey_numbers'] += 1
                    jersey_number_stats['total_jersey_entries'] += player_data['total_jersey_numbers']
                
                if player_data['has_cantonese_data']:
                    jersey_number_stats['players_with_cantonese'] += 1
                
                if player_data['has_jersey_data'] and player_data['has_cantonese_data']:
                    jersey_number_stats['players_with_both'] += 1
                
                # Track teams and jersey numbers
                for jersey_entry in player_data['jersey_numbers']:
                    for team_detail in jersey_entry['team_details']:
                        team_id = team_detail['team_id']
                        jersey_number_stats['unique_teams_with_jersey_data'].add(team_id)
                        
                        if team_detail['has_cantonese']:
                            jersey_number_stats['teams_with_cantonese_names'].add(team_id)
                        
                        # Build team to jersey numbers mapping
                        if team_id not in jersey_number_stats['jersey_numbers_by_team']:
                            jersey_number_stats['jersey_numbers_by_team'][team_id] = []
                        
                        jersey_number_stats['jersey_numbers_by_team'][team_id].append({
                            'player_id': player_id,
                            'player_name_english': player_data['player_names']['english'],
                            'player_name_cantonese': player_data['player_names']['cantonese_best'],
                            'player_has_cantonese': player_data['player_names']['cantonese_lang'] != 'none',
                            'jersey_number': jersey_entry['number'],
                            'start_year': jersey_entry['start_year'],
                            'end_year': jersey_entry['end_year'],
                            'is_current': jersey_entry['is_current'],
                            'team_name_english': team_detail['name'],
                            'team_name_cantonese': team_detail['cantonese_name'],
                            'team_has_cantonese': team_detail['has_cantonese']
                        })
                    
        except Exception as e:
            print(f"Error processing {filename}: {e}")
    
    # Convert sets to counts and lists for final stats
    jersey_number_stats['unique_teams_count'] = len(jersey_number_stats['unique_teams_with_jersey_data'])
    jersey_number_stats['teams_with_cantonese_count'] = len(jersey_number_stats['teams_with_cantonese_names'])
    jersey_number_stats['unique_teams_with_jersey_data'] = list(jersey_number_stats['unique_teams_with_jersey_data'])
    jersey_number_stats['teams_with_cantonese_names'] = list(jersey_number_stats['teams_with_cantonese_names'])
    
    return {
        'players': all_players,
        'jersey_number_stats': jersey_number_stats,
        'processing_info': {
            'total_files_processed': len(files),
            'players_with_data': len(all_players),
            'cache_info': cache_info
        }
    }


if __name__ == "__main__":
    import time
    
    directory_path = "./data/soccer/intermediate/football_players_triples"
    cache_dir = "./data/soccer/cantonese_name_mapping"
    
    if not os.path.exists(directory_path):
        print(f"Directory not found: {directory_path}")
        exit(1)
    
    # Measure performance
    start_time = time.time()
    
    # Process all players for jersey number extraction
    print("Starting comprehensive analysis of all players for jersey number extraction...")
    print("Using cached Cantonese names for improved performance...")
    all_data = process_all_players_jersey_numbers(directory_path, cache_dir)
    
    # Prepare output data
    output_data = {
        'metadata': {
            'extraction_date': datetime.now().isoformat(),
            'total_players_processed': all_data['processing_info']['total_files_processed'],
            'players_with_jersey_data': all_data['jersey_number_stats']['players_with_jersey_numbers'],
            'players_with_cantonese_data': all_data['jersey_number_stats']['players_with_cantonese'],
            'players_with_both_jersey_and_cantonese': all_data['jersey_number_stats']['players_with_both'],
            'total_jersey_number_entries': all_data['jersey_number_stats']['total_jersey_entries'],
            'unique_teams_with_jersey_data': all_data['jersey_number_stats']['unique_teams_count'],
            'teams_with_cantonese_names': all_data['jersey_number_stats']['teams_with_cantonese_count'],
            'cache_info': all_data['jersey_number_stats']['cache_info']
        },
        'players': all_data['players'],
        'jersey_numbers_by_team': all_data['jersey_number_stats']['jersey_numbers_by_team'],
        'teams_with_jersey_data': all_data['jersey_number_stats']['unique_teams_with_jersey_data'],
        'teams_with_cantonese_names': all_data['jersey_number_stats']['teams_with_cantonese_names'],
        'processing_info': all_data['processing_info']
    }
    
    # Write to JSON file
    output_file = "./data/soccer/intermediate/football_players_jersey_numbers.json"
    print(f"Writing jersey number data to {output_file}...")
    
    # Ensure output directory exists
    os.makedirs("./data/soccer/intermediate", exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    processing_time = time.time() - start_time
    
    print("\n" + "="*80)
    print("JERSEY NUMBER EXTRACTION COMPLETE")
    print("="*80)
    print(f"✓ Total players processed: {all_data['processing_info']['total_files_processed']}")
    print(f"✓ Players with jersey number data: {all_data['jersey_number_stats']['players_with_jersey_numbers']}")
    print(f"✓ Players with Cantonese names: {all_data['jersey_number_stats']['players_with_cantonese']}")
    print(f"✓ Players with both jersey numbers and Cantonese names: {all_data['jersey_number_stats']['players_with_both']}")
    print(f"✓ Total jersey number entries: {all_data['jersey_number_stats']['total_jersey_entries']}")
    print(f"✓ Unique teams with jersey number data: {all_data['jersey_number_stats']['unique_teams_count']}")
    print(f"✓ Teams with Cantonese names: {all_data['jersey_number_stats']['teams_with_cantonese_count']}")
    print(f"✓ Data saved to: {output_file}")
    print(f"✓ Processing time: {processing_time:.2f} seconds")
    print(f"✓ {all_data['jersey_number_stats']['cache_info']}")
    
    print("\nJersey number dataset can be used for:")
    print("  • Cantonese benchmark questions about player jersey numbers")
    print("  • Jersey number history and team associations")
    print("  • Player identification through jersey numbers")
    print("  • Team jersey number analysis")
    print("  • Bilingual jersey number queries")
    print("  • Cross-referencing with club affiliation data")
