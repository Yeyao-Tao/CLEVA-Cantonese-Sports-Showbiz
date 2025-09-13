#!/usr/bin/env python3
"""
Improved script to extract ALL player club information from WikiData JSONLD files.

This version correctly extracts both current and historical clubs by focusing
on the detailed statement objects rather than the simplified P54 property.

Outputs structured data for all players to support Cantonese benchmark construction.
"""

import json
import os
import csv
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import sys

# Add the current directory to Python path to import utils
sys.path.append(os.path.dirname(__file__))

from utils.jsonld_reader import (
    extract_entity_names,
    load_jsonld_file
)
from utils.cantonese_utils import (
    load_paranames_cantonese,
    get_best_cantonese_name,
    load_cached_cantonese_names,
    get_entity_names_from_cache
)
from utils.date_utils import parse_date
from utils.file_utils import extract_player_id_from_filename


def teams_overlap(team1_info, team2_info):
    """Check if two team memberships overlap in time."""
    start1 = parse_date(team1_info.get('start_date'))
    end1 = parse_date(team1_info.get('end_date'))
    start2 = parse_date(team2_info.get('start_date'))
    end2 = parse_date(team2_info.get('end_date'))
    
    # If any date is missing, we can't determine overlap
    if not all([start1, start2]):
        return False
    
    # If either club is current (no end date), use current year
    current_year = 2025
    if end1 is None:
        end1 = current_year
    if end2 is None:
        end2 = current_year
    
    # Check if time periods overlap
    return not (end1 < start2 or end2 < start1)


def categorize_teams(all_affiliations):
    """
    Categorize team affiliations into clubs, national teams, and youth teams.
    Returns tuple of (clubs, national_teams, youth_teams).
    """
    clubs = []
    national_teams = []
    youth_teams = []
    
    for team in all_affiliations:
        description = team.get('description', '').lower()
        name = team.get('name', '').lower()
        
        # Check for youth teams first
        if any(keyword in description for keyword in ['under-', 'youth', 'u-']):
            youth_teams.append(team)
        elif any(keyword in name for keyword in ['under-', 'u-', 'youth']):
            youth_teams.append(team)
        # Check for national teams
        elif 'national' in description or 'national' in name:
            national_teams.append(team)
        # Everything else is considered a club
        else:
            clubs.append(team)
    
    return clubs, national_teams, youth_teams


def extract_all_teams(jsonld_file_path: str, cached_players: Dict = None, cached_teams: Dict = None) -> Dict[str, Any]:
    """
    Extract ALL team information for a football player from WikiData JSONLD.
    Now uses cached Cantonese names for improved performance.
    
    Args:
        jsonld_file_path: Path to the JSONLD file containing player data
        cached_players: Dictionary of cached player names
        cached_teams: Dictionary of cached team names
        
    Returns:
        Dictionary containing complete player and team information with Cantonese names
    """
    with open(jsonld_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    result = {
        'player_id': None,
        'player_names': {},  # Will contain English and Cantonese names
        'all_affiliations': [],  # All team affiliations (clubs + national teams + youth teams)
        'clubs': [],  # Professional club teams only
        'national_teams': [],  # National team affiliations only
        'current_clubs': [],
        'former_clubs': [],
        'current_national_teams': [],
        'former_national_teams': [],
        'total_affiliations': 0,
        'career_span_years': None,
        'file_path': jsonld_file_path,
        'has_cantonese_data': False  # Track if any Cantonese names found
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
    
    # Extract ALL team information from detailed statements
    team_statements = []
    for item in data.get('@graph', []):
        # Look for ALL P54 statements with detailed information
        item_type = item.get('@type')
        is_statement = False
        
        if isinstance(item_type, list):
            is_statement = 'wikibase:Statement' in item_type
        elif isinstance(item_type, str):
            is_statement = item_type == 'wikibase:Statement'
        
        if is_statement and 'ps:P54' in item:
            
            team_id = item.get('ps:P54', '').replace('wd:', '')
            start_date = item.get('P580')  # start time
            end_date = item.get('P582')    # end time
            
            # Check if this is a current team (no end date or special marker)
            is_current = (end_date is None or 
                         (isinstance(end_date, dict) and end_date.get('@id', '').startswith('_:')))
            
            team_info = {
                'club_id': team_id,  # Keep 'club_id' for backward compatibility
                'start_date': start_date,
                'end_date': end_date,
                'start_year': parse_date(start_date),
                'end_year': parse_date(end_date),
                'is_current': is_current,
                'club_names': {},  # Will contain all names (English and Cantonese)
                'name': 'Unknown',  # English name for backward compatibility
                'description': '',  # English description for backward compatibility
                'cantonese_name': 'Unknown',  # Best Cantonese name
                'has_cantonese': False  # Whether this team has Cantonese names
            }
            
            team_statements.append(team_info)
    
    # Extract team names and descriptions (English and Cantonese) from the JSONLD data
    for team_info in team_statements:
        team_id = team_info['club_id']  # Using club_id field for backward compatibility
        if team_id:
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
            team_info['club_names'] = team_names
            
            # Set backward compatibility fields
            team_info['name'] = team_names['english']
            team_info['description'] = team_names['description_english']
            team_info['cantonese_name'] = team_names['cantonese_best']
            team_info['has_cantonese'] = team_names['cantonese_lang'] != 'none'
            
            # Track if any team has Cantonese data
            if team_info['has_cantonese']:
                result['has_cantonese_data'] = True
        
        result['all_affiliations'].append(team_info)
    
    # Categorize teams into clubs, national teams, and youth teams (filter out youth teams)
    clubs, national_teams, youth_teams = categorize_teams(result['all_affiliations'])
    result['clubs'] = clubs
    result['national_teams'] = national_teams
    # Note: youth_teams are filtered out and not included in the result
    
    # Separate current and former for both clubs and national teams
    result['current_clubs'] = [team for team in clubs if team['is_current']]
    result['former_clubs'] = [team for team in clubs if not team['is_current']]
    result['current_national_teams'] = [team for team in national_teams if team['is_current']]
    result['former_national_teams'] = [team for team in national_teams if not team['is_current']]
    
    result['total_affiliations'] = len(result['all_affiliations'])
    
    # Calculate career span
    years = [team.get('start_year') for team in result['all_affiliations'] if team.get('start_year')]
    if years:
        result['career_span_years'] = {
            'start': min(years),
            'end': max([team.get('end_year') for team in result['all_affiliations'] if team.get('end_year')] + [2025])
        }
    
    return result


def process_all_players(directory_path: str, cache_dir: str = None) -> Dict[str, Any]:
    """Process all player files and return structured data using cached Cantonese names for improved performance."""
    
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
    club_to_players = {}  # Map club_id to list of players who played there
    national_team_to_players = {}  # Map national_team_id to list of players who played there
    cantonese_stats = {
        'players_with_cantonese': 0,
        'clubs_with_cantonese': set(),
        'national_teams_with_cantonese': set(),
        'total_cantonese_club_entries': 0,
        'total_cantonese_national_team_entries': 0,
        'cantonese_from_wikidata': 0,
        'cantonese_from_paranames': 0,
        'clubs_enhanced_by_paranames': set(),
        'national_teams_enhanced_by_paranames': set(),
        'cache_info': cache_info
    }
    
    files = [f for f in os.listdir(directory_path) if f.endswith('.jsonld')]
    
    print(f"Processing {len(files)} player files...")
    
    for i, filename in enumerate(files, 1):
        if i % 10 == 0:
            print(f"Processed {i}/{len(files)} files...")
            
        file_path = os.path.join(directory_path, filename)
        
        try:
            player_data = extract_all_teams(file_path, cached_players, cached_teams)
            player_id = player_data['player_id']
            
            if player_id:
                all_players[player_id] = player_data
                
                # Track Cantonese statistics
                if player_data['has_cantonese_data']:
                    cantonese_stats['players_with_cantonese'] += 1
                
                # Track source of player Cantonese names
                if player_data['player_names']['cantonese_source'] == 'wikidata':
                    cantonese_stats['cantonese_from_wikidata'] += 1
                elif player_data['player_names']['cantonese_source'] == 'paranames':
                    cantonese_stats['cantonese_from_paranames'] += 1
                
                # Build club-to-players and national-team-to-players mappings
                for club in player_data['clubs']:
                    club_id = club['club_id']
                    if club_id not in club_to_players:
                        club_to_players[club_id] = []
                    
                    # Track clubs with Cantonese names and their sources
                    if club['has_cantonese']:
                        cantonese_stats['clubs_with_cantonese'].add(club_id)
                        cantonese_stats['total_cantonese_club_entries'] += 1
                        
                        # Track if this club got its Cantonese name from ParaNames
                        if club['club_names'].get('cantonese_source') == 'paranames':
                            cantonese_stats['clubs_enhanced_by_paranames'].add(club_id)
                    
                    club_to_players[club_id].append({
                        'player_id': player_id,
                        'player_name_english': player_data['player_names']['english'],
                        'player_name_cantonese': player_data['player_names']['cantonese_best'],
                        'player_has_cantonese': player_data['player_names']['cantonese_lang'] != 'none',
                        'start_year': club.get('start_year'),
                        'end_year': club.get('end_year'),
                        'is_current': club['is_current']
                    })
                
                for national_team in player_data['national_teams']:
                    team_id = national_team['club_id']
                    if team_id not in national_team_to_players:
                        national_team_to_players[team_id] = []
                    
                    # Track national teams with Cantonese names and their sources
                    if national_team['has_cantonese']:
                        cantonese_stats['national_teams_with_cantonese'].add(team_id)
                        cantonese_stats['total_cantonese_national_team_entries'] += 1
                        
                        # Track if this national team got its Cantonese name from ParaNames
                        if national_team['club_names'].get('cantonese_source') == 'paranames':
                            cantonese_stats['national_teams_enhanced_by_paranames'].add(team_id)
                    
                    national_team_to_players[team_id].append({
                        'player_id': player_id,
                        'player_name_english': player_data['player_names']['english'],
                        'player_name_cantonese': player_data['player_names']['cantonese_best'],
                        'player_has_cantonese': player_data['player_names']['cantonese_lang'] != 'none',
                        'start_year': national_team.get('start_year'),
                        'end_year': national_team.get('end_year'),
                        'is_current': national_team['is_current']
                    })
                    
        except Exception as e:
            print(f"Error processing {filename}: {e}")
    
    # Convert sets to counts for final stats
    cantonese_stats['unique_clubs_with_cantonese'] = len(cantonese_stats['clubs_with_cantonese'])
    cantonese_stats['unique_national_teams_with_cantonese'] = len(cantonese_stats['national_teams_with_cantonese'])
    cantonese_stats['unique_clubs_enhanced_by_paranames'] = len(cantonese_stats['clubs_enhanced_by_paranames'])
    cantonese_stats['unique_national_teams_enhanced_by_paranames'] = len(cantonese_stats['national_teams_enhanced_by_paranames'])
    cantonese_stats['clubs_with_cantonese'] = list(cantonese_stats['clubs_with_cantonese'])
    cantonese_stats['national_teams_with_cantonese'] = list(cantonese_stats['national_teams_with_cantonese'])
    cantonese_stats['clubs_enhanced_by_paranames'] = list(cantonese_stats['clubs_enhanced_by_paranames'])
    cantonese_stats['national_teams_enhanced_by_paranames'] = list(cantonese_stats['national_teams_enhanced_by_paranames'])
    
    return {
        'players': all_players,
        'club_to_players': club_to_players,
        'national_team_to_players': national_team_to_players,
        'cantonese_statistics': cantonese_stats,
        'processing_info': {
            'total_files': len(files),
            'successfully_processed': len(all_players),
            'timestamp': datetime.now().isoformat()
        }
    }


def find_potential_teammates(all_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Find pairs of players who were potentially teammates, separated by club and national team affiliations.
    Returns dictionary with 'club_teammates' and 'national_teammates' lists.
    """
    
    club_teammates = []
    national_teammates = []
    
    # Build separate mappings for clubs and national teams
    club_to_players = {}
    national_team_to_players = {}
    
    # Populate mappings
    for player_id, player_data in all_data['players'].items():
        # Process club affiliations
        for club in player_data['clubs']:
            club_id = club['club_id']
            if club_id not in club_to_players:
                club_to_players[club_id] = []
            
            club_to_players[club_id].append({
                'player_id': player_id,
                'player_name_english': player_data['player_names']['english'],
                'player_name_cantonese': player_data['player_names']['cantonese_best'],
                'player_has_cantonese': player_data['player_names']['cantonese_lang'] != 'none',
                'start_year': club.get('start_year'),
                'end_year': club.get('end_year'),
                'is_current': club['is_current']
            })
        
        # Process national team affiliations
        for national_team in player_data['national_teams']:
            team_id = national_team['club_id']  # Using same field name for consistency
            if team_id not in national_team_to_players:
                national_team_to_players[team_id] = []
            
            national_team_to_players[team_id].append({
                'player_id': player_id,
                'player_name_english': player_data['player_names']['english'],
                'player_name_cantonese': player_data['player_names']['cantonese_best'],
                'player_has_cantonese': player_data['player_names']['cantonese_lang'] != 'none',
                'start_year': national_team.get('start_year'),
                'end_year': national_team.get('end_year'),
                'is_current': national_team['is_current']
            })
    
    # Find club teammates
    for club_id, players_list in club_to_players.items():
        if len(players_list) < 2:
            continue
            
        # Check all pairs of players at this club
        for i, player1 in enumerate(players_list):
            for player2 in players_list[i+1:]:
                
                # Create club info for overlap checking
                club1_info = {
                    'start_date': f"{player1['start_year']}-01-01T00:00:00Z" if player1.get('start_year') else None,
                    'end_date': f"{player1['end_year']}-01-01T00:00:00Z" if player1.get('end_year') else None
                }
                club2_info = {
                    'start_date': f"{player2['start_year']}-01-01T00:00:00Z" if player2.get('start_year') else None,
                    'end_date': f"{player2['end_year']}-01-01T00:00:00Z" if player2.get('end_year') else None
                }
                
                if teams_overlap(club1_info, club2_info):
                    # Get club names (English and Cantonese)
                    team_names = {
                        'english': "Unknown Club",
                        'cantonese': "Unknown Club",
                        'has_cantonese': False
                    }
                    
                    # Find club names from player data
                    for player_data in all_data['players'].values():
                        for club in player_data['clubs']:
                            if club['club_id'] == club_id:
                                team_names['english'] = club['name']
                                team_names['cantonese'] = club['cantonese_name']
                                team_names['has_cantonese'] = club['has_cantonese']
                                break
                        if team_names['english'] != "Unknown Club":
                            break
                    
                    club_teammates.append({
                        'player1': {
                            'id': player1['player_id'],
                            'name_english': player1['player_name_english'],
                            'name_cantonese': player1['player_name_cantonese'],
                            'has_cantonese': player1['player_has_cantonese'],
                            'start_year': player1.get('start_year'),
                            'end_year': player1.get('end_year')
                        },
                        'player2': {
                            'id': player2['player_id'], 
                            'name_english': player2['player_name_english'],
                            'name_cantonese': player2['player_name_cantonese'],
                            'has_cantonese': player2['player_has_cantonese'],
                            'start_year': player2.get('start_year'),
                            'end_year': player2.get('end_year')
                        },
                        'team': {
                            'id': club_id,
                            'name_english': team_names['english'],
                            'name_cantonese': team_names['cantonese'],
                            'has_cantonese': team_names['has_cantonese'],
                            'type': 'club'
                        },
                        'has_any_cantonese': (player1['player_has_cantonese'] or 
                                            player2['player_has_cantonese'] or 
                                            team_names['has_cantonese'])
                    })
    
    # Find national teammates (similar logic)
    for team_id, players_list in national_team_to_players.items():
        if len(players_list) < 2:
            continue
            
        # Check all pairs of players at this national team
        for i, player1 in enumerate(players_list):
            for player2 in players_list[i+1:]:
                
                # Create team info for overlap checking
                team1_info = {
                    'start_date': f"{player1['start_year']}-01-01T00:00:00Z" if player1.get('start_year') else None,
                    'end_date': f"{player1['end_year']}-01-01T00:00:00Z" if player1.get('end_year') else None
                }
                team2_info = {
                    'start_date': f"{player2['start_year']}-01-01T00:00:00Z" if player2.get('start_year') else None,
                    'end_date': f"{player2['end_year']}-01-01T00:00:00Z" if player2.get('end_year') else None
                }
                
                if teams_overlap(team1_info, team2_info):
                    # Get national team names (English and Cantonese)
                    team_names = {
                        'english': "Unknown National Team",
                        'cantonese': "Unknown National Team",
                        'has_cantonese': False
                    }
                    
                    # Find national team names from player data
                    for player_data in all_data['players'].values():
                        for national_team in player_data['national_teams']:
                            if national_team['club_id'] == team_id:
                                team_names['english'] = national_team['name']
                                team_names['cantonese'] = national_team['cantonese_name']
                                team_names['has_cantonese'] = national_team['has_cantonese']
                                break
                        if team_names['english'] != "Unknown National Team":
                            break
                    
                    national_teammates.append({
                        'player1': {
                            'id': player1['player_id'],
                            'name_english': player1['player_name_english'],
                            'name_cantonese': player1['player_name_cantonese'],
                            'has_cantonese': player1['player_has_cantonese'],
                            'start_year': player1.get('start_year'),
                            'end_year': player1.get('end_year')
                        },
                        'player2': {
                            'id': player2['player_id'], 
                            'name_english': player2['player_name_english'],
                            'name_cantonese': player2['player_name_cantonese'],
                            'has_cantonese': player2['player_has_cantonese'],
                            'start_year': player2.get('start_year'),
                            'end_year': player2.get('end_year')
                        },
                        'team': {
                            'id': team_id,
                            'name_english': team_names['english'],
                            'name_cantonese': team_names['cantonese'],
                            'has_cantonese': team_names['has_cantonese'],
                            'type': 'national_team'
                        },
                        'has_any_cantonese': (player1['player_has_cantonese'] or 
                                            player2['player_has_cantonese'] or 
                                            team_names['has_cantonese'])
                    })
    
    return {
        'club_teammates': club_teammates,
        'national_teammates': national_teammates
    }


def analyze_single_player(file_path: str, paranames_cantonese: Dict[str, Dict[str, str]] = None) -> None:
    """Analyze a single player file and display comprehensive team information with Cantonese names from both WikiData and ParaNames."""
    
    print(f"\nAnalyzing: {os.path.basename(file_path)}")
    print("=" * 60)
    
    try:
        team_info = extract_all_teams(file_path, cached_players, cached_teams)
        
        # Display player information
        player_names = team_info['player_names']
        print(f"Player: {player_names['english']} ({team_info['player_id']})")
        if player_names['cantonese_lang'] != 'none':
            source_info = f" (from {player_names['cantonese_source']})" if 'cantonese_source' in player_names else ""
            print(f"Cantonese: {player_names['cantonese_best']} ({player_names['cantonese_lang']}){source_info}")
        print(f"Total affiliations in career: {team_info['total_affiliations']}")
        print(f"Clubs: {len(team_info['clubs'])}, National teams: {len(team_info['national_teams'])}")
        print(f"Has Cantonese data: {team_info['has_cantonese_data']}")
        
        if team_info['current_clubs']:
            print(f"\nCurrent Club(s) ({len(team_info['current_clubs'])}):")
            for club in team_info['current_clubs']:
                start_year = club['start_date'][:4] if isinstance(club['start_date'], str) else "?"
                print(f"  ✓ {club.get('name', 'Unknown')} ({club['club_id']}) - {start_year} to present")
                if club['has_cantonese']:
                    source_info = f" (from {club['club_names'].get('cantonese_source', 'unknown')})" if 'cantonese_source' in club['club_names'] else ""
                    print(f"    粵語: {club['cantonese_name']}{source_info}")
                if club.get('description'):
                    print(f"    └── {club['description']}")
        
        if team_info['current_national_teams']:
            print(f"\nCurrent National Team(s) ({len(team_info['current_national_teams'])}):")
            for team in team_info['current_national_teams']:
                start_year = team['start_date'][:4] if isinstance(team['start_date'], str) else "?"
                print(f"  ✓ {team.get('name', 'Unknown')} ({team['club_id']}) - {start_year} to present")
                if team['has_cantonese']:
                    source_info = f" (from {team['club_names'].get('cantonese_source', 'unknown')})" if 'cantonese_source' in team['club_names'] else ""
                    print(f"    粵語: {team['cantonese_name']}{source_info}")
                if team.get('description'):
                    print(f"    └── {team['description']}")
        
        if team_info['former_clubs']:
            print(f"\nFormer Clubs ({len(team_info['former_clubs'])}):")
            # Sort by start date (most recent first)
            sorted_former = sorted(team_info['former_clubs'], 
                                 key=lambda x: x.get('start_date', ''), reverse=True)
            
            for club in sorted_former:
                start_year = club['start_date'][:4] if isinstance(club['start_date'], str) else "?"
                end_year = club['end_date'][:4] if isinstance(club['end_date'], str) and club['end_date'] else "?"
                period = f"{start_year}-{end_year}" if end_year != "?" else f"{start_year}-?"
                
                print(f"  • {club.get('name', 'Unknown')} ({club['club_id']}) - {period}")
                if club['has_cantonese']:
                    source_info = f" (from {club['club_names'].get('cantonese_source', 'unknown')})" if 'cantonese_source' in club['club_names'] else ""
                    print(f"    粵語: {club['cantonese_name']}{source_info}")
                if club.get('description'):
                    print(f"    └── {club['description']}")
        
        if team_info['former_national_teams']:
            print(f"\nFormer National Teams ({len(team_info['former_national_teams'])}):")
            # Sort by start date (most recent first)
            sorted_former_national = sorted(team_info['former_national_teams'], 
                                          key=lambda x: x.get('start_date', ''), reverse=True)
            
            for team in sorted_former_national:
                start_year = team['start_date'][:4] if isinstance(team['start_date'], str) else "?"
                end_year = team['end_date'][:4] if isinstance(team['end_date'], str) and team['end_date'] else "?"
                period = f"{start_year}-{end_year}" if end_year != "?" else f"{start_year}-?"
                
                print(f"  • {team.get('name', 'Unknown')} ({team['club_id']}) - {period}")
                if team['has_cantonese']:
                    source_info = f" (from {team['club_names'].get('cantonese_source', 'unknown')})" if 'cantonese_source' in team['club_names'] else ""
                    print(f"    粵語: {team['cantonese_name']}{source_info}")
                if team.get('description'):
                    print(f"    └── {team['description']}")
        
        print("\nComplete Career Timeline with Cantonese Names:")
        # Sort all affiliations by start date
        all_affiliations_sorted = sorted(team_info['all_affiliations'], 
                                        key=lambda x: x.get('start_date', ''))
        
        for i, affiliation in enumerate(all_affiliations_sorted, 1):
            start_year = affiliation['start_date'][:4] if isinstance(affiliation['start_date'], str) else "?"
            end_year = affiliation['end_date'][:4] if isinstance(affiliation['end_date'], str) and affiliation['end_date'] else "present"
            status = "[CURRENT]" if affiliation['is_current'] else "[FORMER]"
            
            # Determine team type
            team_type = ""
            if affiliation in team_info['clubs']:
                team_type = " [CLUB]"
            elif affiliation in team_info['national_teams']:
                team_type = " [NATIONAL]"
            
            # Enhanced indicators for Cantonese names and their sources
            cantonese_indicator = ""
            if affiliation['has_cantonese']:
                source = affiliation['club_names'].get('cantonese_source', 'unknown')
                if source == 'wikidata':
                    cantonese_indicator = " 🇭🇰"
                elif source == 'paranames':
                    cantonese_indicator = " 🇭🇰📚"  # Book emoji to indicate ParaNames source
                else:
                    cantonese_indicator = " 🇭🇰"
            
            print(f"  {i:2d}. {start_year}-{end_year}: {affiliation.get('name', 'Unknown')}{cantonese_indicator}{team_type} {status}")
            if affiliation['has_cantonese']:
                source_info = f" (from {affiliation['club_names'].get('cantonese_source', 'unknown')})" if 'cantonese_source' in affiliation['club_names'] else ""
                print(f"      粵語: {affiliation['cantonese_name']}{source_info}")
        
    except Exception as e:
        print(f"Error processing file: {e}")


if __name__ == "__main__":
    import time
    
    directory_path = "./data/soccer/intermediate/football_players_triples"
    cache_dir = "./data/soccer/cantonese_name_mapping"
    
    if not os.path.exists(directory_path):
        print(f"Directory not found: {directory_path}")
        exit(1)
    
    # Measure performance
    start_time = time.time()
    
    # Process all players using cached names
    print("Starting comprehensive analysis of all players with Cantonese name extraction...")
    print("Using cached Cantonese names for improved performance...")
    all_data = process_all_players(directory_path, cache_dir)
    
    # Filter to keep only players with Cantonese names
    print("Filtering players to keep only those with Cantonese names...")
    original_player_count = len(all_data['players'])
    filtered_players = {
        player_id: player_data 
        for player_id, player_data in all_data['players'].items() 
        if player_data['has_cantonese_data']
    }
    
    # Update the players dictionary
    all_data['players'] = filtered_players
    
    # Rebuild club_to_players and national_team_to_players mappings with filtered players only
    print("Rebuilding club and national team mappings with filtered players...")
    filtered_club_to_players = {}
    filtered_national_team_to_players = {}
    
    for player_id, player_data in filtered_players.items():
        for club in player_data['clubs']:
            club_id = club['club_id']
            if club_id not in filtered_club_to_players:
                filtered_club_to_players[club_id] = []
            
            filtered_club_to_players[club_id].append({
                'player_id': player_id,
                'player_name_english': player_data['player_names']['english'],
                'player_name_cantonese': player_data['player_names']['cantonese_best'],
                'player_has_cantonese': player_data['player_names']['cantonese_lang'] != 'none',
                'start_year': club.get('start_year'),
                'end_year': club.get('end_year'),
                'is_current': club['is_current']
            })
        
        for national_team in player_data['national_teams']:
            team_id = national_team['club_id']
            if team_id not in filtered_national_team_to_players:
                filtered_national_team_to_players[team_id] = []
            
            filtered_national_team_to_players[team_id].append({
                'player_id': player_id,
                'player_name_english': player_data['player_names']['english'],
                'player_name_cantonese': player_data['player_names']['cantonese_best'],
                'player_has_cantonese': player_data['player_names']['cantonese_lang'] != 'none',
                'start_year': national_team.get('start_year'),
                'end_year': national_team.get('end_year'),
                'is_current': national_team['is_current']
            })
    
    all_data['club_to_players'] = filtered_club_to_players
    all_data['national_team_to_players'] = filtered_national_team_to_players
    
    # Update Cantonese statistics for filtered data
    filtered_cantonese_stats = {
        'players_with_cantonese': len(filtered_players),
        'clubs_with_cantonese': set(),
        'national_teams_with_cantonese': set(),
        'total_cantonese_club_entries': 0,
        'total_cantonese_national_team_entries': 0,
        'original_player_count': original_player_count,
        'filtered_player_count': len(filtered_players),
        'filtering_ratio': round(len(filtered_players) / original_player_count * 100, 2)
    }
    
    # Count clubs and national teams with Cantonese names in filtered data
    for player_data in filtered_players.values():
        for club in player_data['clubs']:
            if club['has_cantonese']:
                filtered_cantonese_stats['clubs_with_cantonese'].add(club['club_id'])
                filtered_cantonese_stats['total_cantonese_club_entries'] += 1
        
        for national_team in player_data['national_teams']:
            if national_team['has_cantonese']:
                filtered_cantonese_stats['national_teams_with_cantonese'].add(national_team['club_id'])
                filtered_cantonese_stats['total_cantonese_national_team_entries'] += 1
    
    filtered_cantonese_stats['unique_clubs_with_cantonese'] = len(filtered_cantonese_stats['clubs_with_cantonese'])
    filtered_cantonese_stats['unique_national_teams_with_cantonese'] = len(filtered_cantonese_stats['national_teams_with_cantonese'])
    filtered_cantonese_stats['clubs_with_cantonese'] = list(filtered_cantonese_stats['clubs_with_cantonese'])
    filtered_cantonese_stats['national_teams_with_cantonese'] = list(filtered_cantonese_stats['national_teams_with_cantonese'])
    
    all_data['cantonese_statistics'] = filtered_cantonese_stats
    
    # Extract all unique clubs and national teams with their information
    print("Extracting all unique clubs and national teams information...")
    all_clubs = {}
    all_national_teams = {}
    
    for player_data in filtered_players.values():
        for club in player_data['clubs']:
            club_id = club['club_id']
            if club_id not in all_clubs:
                all_clubs[club_id] = {
                    'name_english': club['name'],
                    'name_cantonese': club['cantonese_name'],
                    'has_cantonese': club['has_cantonese'],
                    'description_english': club['description'],
                    'club_names': club['club_names'],
                    'player_count': 0  # Will be updated below
                }
            # Count unique players for this club
            all_clubs[club_id]['player_count'] = len(filtered_club_to_players.get(club_id, []))
        
        for national_team in player_data['national_teams']:
            team_id = national_team['club_id']
            if team_id not in all_national_teams:
                all_national_teams[team_id] = {
                    'name_english': national_team['name'],
                    'name_cantonese': national_team['cantonese_name'],
                    'has_cantonese': national_team['has_cantonese'],
                    'description_english': national_team['description'],
                    'club_names': national_team['club_names'],
                    'player_count': 0  # Will be updated below
                }
            # Count unique players for this national team
            all_national_teams[team_id]['player_count'] = len(filtered_national_team_to_players.get(team_id, []))
    
    # Find potential teammates with filtered data (separated by club and national team)
    print("Finding potential teammates among players with Cantonese names...")
    teammates_data = find_potential_teammates(all_data)
    club_teammates = teammates_data['club_teammates']
    national_teammates = teammates_data['national_teammates']
    
    # Prepare enhanced output data with Cantonese information (filtered)
    cantonese_stats = all_data['cantonese_statistics']
    
    output_data = {
        'metadata': {
            'description': 'Football player club affiliations extracted from WikiData for Cantonese benchmark construction - FILTERED for players with Cantonese names only',
            'purpose': 'Support generation of questions about player careers and teammate relationships with Cantonese names',
            'data_structure': {
                'players': 'Dictionary of player_id -> player data with clubs and national_teams lists',
                'club_to_players_mapping': 'Dictionary of club_id -> list of players who played there',
                'national_team_to_players_mapping': 'Dictionary of national_team_id -> list of players who played there',
                'all_clubs': 'Dictionary of club_id -> club data with English/Cantonese names and player counts',
                'all_national_teams': 'Dictionary of national_team_id -> national team data with English/Cantonese names and player counts',
                'club_teammates': 'Array of player pairs who potentially played together at the same club',
                'national_teammates': 'Array of player pairs who potentially played together for the same national team',
                'note': 'Youth teams are filtered out entirely. Clubs and national teams are separated.'
            },
            'extraction_date': datetime.now().isoformat(),
            'total_players': len(all_data['players']),
            'total_club_teammate_pairs': len(club_teammates),
            'total_national_teammate_pairs': len(national_teammates),
            'filtering_info': {
                'original_player_count': cantonese_stats['original_player_count'],
                'filtered_player_count': cantonese_stats['filtered_player_count'],
                'filtering_ratio': cantonese_stats['filtering_ratio'],
                'filter_criteria': 'Players must have valid Cantonese names (yue or zh-hk language codes)'
            },
            'cantonese_coverage': {
                'players_with_cantonese_names': cantonese_stats['players_with_cantonese'],
                'unique_clubs_with_cantonese_names': cantonese_stats['unique_clubs_with_cantonese'],
                'unique_national_teams_with_cantonese_names': cantonese_stats['unique_national_teams_with_cantonese'],
                'total_club_entries_with_cantonese': cantonese_stats['total_cantonese_club_entries'],
                'total_national_team_entries_with_cantonese': cantonese_stats['total_cantonese_national_team_entries'],
                'coverage_percentage_players': 100.0,  # 100% since all remaining players have Cantonese names
                'club_teammate_pairs_with_cantonese': len([t for t in club_teammates if t['has_any_cantonese']]),
                'national_teammate_pairs_with_cantonese': len([t for t in national_teammates if t['has_any_cantonese']]),
                'paranames_enhancement': {
                    'players_from_wikidata': cantonese_stats.get('cantonese_from_wikidata', 0),
                    'players_from_paranames': cantonese_stats.get('cantonese_from_paranames', 0),
                    'clubs_enhanced_by_paranames': cantonese_stats.get('unique_clubs_enhanced_by_paranames', 0),
                    'national_teams_enhanced_by_paranames': cantonese_stats.get('unique_national_teams_enhanced_by_paranames', 0),
                    'clubs_enhanced_list': cantonese_stats.get('clubs_enhanced_by_paranames', []),
                    'national_teams_enhanced_list': cantonese_stats.get('national_teams_enhanced_by_paranames', [])
                }
            }
        },
        'players': all_data['players'],
        'club_to_players_mapping': all_data['club_to_players'],
        'national_team_to_players_mapping': all_data['national_team_to_players'],
        'all_clubs': all_clubs,
        'all_national_teams': all_national_teams,
        'club_teammates': club_teammates,
        'national_teammates': national_teammates,
        'processing_info': all_data['processing_info'],
        'cantonese_statistics': cantonese_stats
    }
    
    # Write to JSON file with enhanced name
    output_file = "./data/soccer/intermediate/football_players_clubs_complete.json"
    print(f"Writing filtered data (Cantonese players only) to {output_file}...")
    
    # Ensure output directory exists
    os.makedirs("./data/soccer/intermediate", exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*80)
    print("CANTONESE FILTERING COMPLETE (Enhanced with ParaNames)")
    print("="*80)
    print(f"✓ Original players processed: {cantonese_stats['original_player_count']}")
    print(f"✓ Players with Cantonese names retained: {len(all_data['players'])} ({cantonese_stats['filtering_ratio']}%)")
    print(f"✓ Players without Cantonese names filtered out: {cantonese_stats['original_player_count'] - len(all_data['players'])}")
    print(f"✓ Found {len(all_data['club_to_players'])} unique clubs in filtered data")
    print(f"✓ Found {len(all_data.get('national_team_to_players', {}))} unique national teams in filtered data")
    print(f"✓ All clubs dictionary contains {len(all_clubs)} clubs indexed by club_id")
    print(f"✓ All national teams dictionary contains {len(all_national_teams)} national teams indexed by team_id")
    print(f"✓ Identified {len(club_teammates)} potential club teammate pairs")
    print(f"✓ Identified {len(national_teammates)} potential national teammate pairs")
    print(f"✓ Clubs with Cantonese names: {cantonese_stats['unique_clubs_with_cantonese']}")
    print(f"✓ National teams with Cantonese names: {cantonese_stats.get('unique_national_teams_with_cantonese', 0)}")
    print(f"✓ Clubs enhanced by ParaNames: {cantonese_stats.get('unique_clubs_enhanced_by_paranames', 0)}")
    print(f"✓ National teams enhanced by ParaNames: {cantonese_stats.get('unique_national_teams_enhanced_by_paranames', 0)}")
    print(f"✓ Player names from WikiData: {cantonese_stats.get('cantonese_from_wikidata', 0)}")
    print(f"✓ Player names from ParaNames: {cantonese_stats.get('cantonese_from_paranames', 0)}")
    print(f"✓ Filtered data saved to: {output_file}")
    
    processing_time = time.time() - start_time
    print(f"✓ Processing time: {processing_time:.2f} seconds")
    
    print("\nFiltered dataset contains ONLY players with valid Cantonese names and can be used for:")
    print("  • Cantonese benchmark questions about player club careers")
    print("  • Cantonese benchmark questions about player national team careers")
    print("  • Club teammate relationship questions with Cantonese names")
    print("  • National team teammate relationship questions with Cantonese names")
    print("  • Bilingual player career timelines and transfers")
    print("  • Translation tasks between English and Cantonese player/team names")
    print("  • All questions will have guaranteed Cantonese name coverage")
    print("  • Performance optimized with cached Cantonese names")
    print("  • Youth teams are completely filtered out from the dataset")
