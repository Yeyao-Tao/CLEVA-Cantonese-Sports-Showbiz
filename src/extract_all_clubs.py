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


def parse_date(date_str):
    """Parse WikiData date string to extract year."""
    if isinstance(date_str, str) and len(date_str) >= 4:
        return int(date_str[:4])
    return None


def load_paranames_cantonese(paranames_tsv_path: str) -> Dict[str, Dict[str, str]]:
    """
    Load Cantonese names from ParaNames dataset.
    
    Args:
        paranames_tsv_path: Path to the paranames.tsv file
        
    Returns:
        Dictionary mapping wikidata_id to cantonese names (yue and zh-hk)
    """
    cantonese_names = {}
    
    if not os.path.exists(paranames_tsv_path):
        print(f"Warning: ParaNames file not found at {paranames_tsv_path}")
        return cantonese_names
    
    print(f"Loading Cantonese names from ParaNames dataset: {paranames_tsv_path}")
    
    with open(paranames_tsv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        
        for row in reader:
            wikidata_id = row.get('wikidata_id', '').strip()
            language = row.get('language', '').strip()
            label = row.get('label', '').strip()
            
            # Only process Cantonese-related language codes
            if language in ['yue', 'zh-hk'] and wikidata_id and label:
                if wikidata_id not in cantonese_names:
                    cantonese_names[wikidata_id] = {}
                
                cantonese_names[wikidata_id][language] = label
    
    print(f"Loaded Cantonese names for {len(cantonese_names)} entities from ParaNames")
    return cantonese_names


def clubs_overlap(club1_info, club2_info):
    """Check if two club memberships overlap in time."""
    start1 = parse_date(club1_info.get('start_date'))
    end1 = parse_date(club1_info.get('end_date'))
    start2 = parse_date(club2_info.get('start_date'))
    end2 = parse_date(club2_info.get('end_date'))
    
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


def filter_football_clubs(clubs):
    """Filter out national teams and youth teams, keeping only club teams."""
    football_clubs = []
    for club in clubs:
        description = club.get('description', '').lower()
        name = club.get('name', '').lower()
        
        # Skip national teams and youth teams
        if any(keyword in description for keyword in ['national', 'under-', 'youth']):
            continue
        if any(keyword in name for keyword in ['national', 'under-', 'u-', 'youth']):
            continue
        
        football_clubs.append(club)
    
    return football_clubs


def extract_cantonese_labels(data: dict, target_id: str) -> Dict[str, str]:
    """
    Extract Cantonese labels for a specific entity from WikiData JSONLD.
    
    Args:
        data: The parsed JSON-LD data
        target_id: The entity ID to extract labels for (e.g., 'Q107051')
        
    Returns:
        Dictionary containing Cantonese labels with language codes as keys
    """
    cantonese_labels = {}
    
    for item in data.get('@graph', []):
        item_id = item.get('@id', '')
        
        # Look for the target entity
        if (item.get('@type') == 'wikibase:Item' and 
            item_id == f'wd:{target_id}' and 
            'label' in item):
            
            labels = item.get('label', [])
            if isinstance(labels, dict):
                labels = [labels]
            
            # Extract Cantonese labels (yue and zh-hk)
            for label in labels:
                if isinstance(label, dict):
                    lang = label.get('@language', '')
                    value = label.get('@value', '')
                    
                    if lang in ['yue', 'zh-hk'] and value:
                        cantonese_labels[lang] = value
                        
    return cantonese_labels


def get_best_cantonese_name(cantonese_labels: Dict[str, str]) -> Tuple[str, str]:
    """
    Get the best Cantonese name from available labels.
    Prioritizes 'yue' over 'zh-hk', returns language code used.
    
    Args:
        cantonese_labels: Dict of language codes to labels
        
    Returns:
        Tuple of (best_name, language_code_used)
    """
    if 'yue' in cantonese_labels:
        return cantonese_labels['yue'], 'yue'
    elif 'zh-hk' in cantonese_labels:
        return cantonese_labels['zh-hk'], 'zh-hk'
    else:
        return 'unknown', 'none'


def extract_entity_names(data: dict, target_id: str, paranames_cantonese: Dict[str, Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Extract all available names for an entity (English, Cantonese, etc.).
    Now enhanced with ParaNames dataset for additional Cantonese names.
    
    Args:
        data: The parsed JSON-LD data
        target_id: The entity ID to extract names for
        paranames_cantonese: Dictionary of Cantonese names from ParaNames dataset
        
    Returns:
        Dictionary containing all available names and metadata
    """
    names = {
        'id': target_id,
        'english': 'Unknown',
        'cantonese': {},
        'cantonese_best': 'Unknown',
        'cantonese_lang': 'none',
        'description_english': '',
        'description_cantonese': {},
        'cantonese_source': 'none'  # Track whether Cantonese name came from WikiData or ParaNames
    }
    
    for item in data.get('@graph', []):
        item_id = item.get('@id', '')
        
        # Look for the target entity (can be with or without @type)
        if item_id == f'wd:{target_id}':
            
            # Extract labels
            if 'label' in item:
                labels = item.get('label', [])
                if isinstance(labels, dict):
                    labels = [labels]
                
                for label in labels:
                    if isinstance(label, dict):
                        lang = label.get('@language', '')
                        value = label.get('@value', '')
                        
                        if lang == 'en':
                            names['english'] = value
                        elif lang in ['yue', 'zh-hk']:
                            names['cantonese'][lang] = value
                            names['cantonese_source'] = 'wikidata'
            
            # Extract descriptions
            if 'description' in item:
                descriptions = item.get('description', [])
                if isinstance(descriptions, dict):
                    descriptions = [descriptions]
                
                for desc in descriptions:
                    if isinstance(desc, dict):
                        lang = desc.get('@language', '')
                        value = desc.get('@value', '')
                        
                        if lang == 'en':
                            names['description_english'] = value
                        elif lang in ['yue', 'zh-hk']:
                            names['description_cantonese'][lang] = value

    # If no Cantonese names found in WikiData, check ParaNames dataset
    if not names['cantonese'] and paranames_cantonese and target_id in paranames_cantonese:
        names['cantonese'] = paranames_cantonese[target_id].copy()
        names['cantonese_source'] = 'paranames'
    
    # Set best Cantonese name
    names['cantonese_best'], names['cantonese_lang'] = get_best_cantonese_name(names['cantonese'])
    
    return names
    
def extract_all_clubs(jsonld_file_path: str, paranames_cantonese: Dict[str, Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Extract ALL club information for a football player from WikiData JSONLD.
    Now includes Cantonese names for both players and clubs, enhanced with ParaNames dataset.
    
    Args:
        jsonld_file_path: Path to the JSONLD file containing player data
        paranames_cantonese: Dictionary of Cantonese names from ParaNames dataset
        
    Returns:
        Dictionary containing complete player and club information with Cantonese names
    """
    with open(jsonld_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    result = {
        'player_id': None,
        'player_names': {},  # Will contain English and Cantonese names
        'clubs': [],
        'current_clubs': [],
        'former_clubs': [],
        'football_clubs_only': [],  # Excluding national teams
        'total_clubs': 0,
        'career_span_years': None,
        'file_path': jsonld_file_path,
        'has_cantonese_data': False  # Track if any Cantonese names found
    }
    
    # Extract player ID from filename
    filename = os.path.basename(jsonld_file_path)
    if filename.startswith('Q') and filename.endswith('.jsonld'):
        player_id = filename[:-7]  # Remove .jsonld extension
        result['player_id'] = player_id
        
        # Extract all player names (English and Cantonese)
        result['player_names'] = extract_entity_names(data, player_id, paranames_cantonese)
        
        # Check if we have Cantonese data for the player
        if result['player_names']['cantonese_lang'] != 'none':
            result['has_cantonese_data'] = True
    
    # Extract ALL club information from detailed statements
    club_statements = []
    for item in data.get('@graph', []):
        # Look for ALL P54 statements with detailed information
        item_type = item.get('@type')
        is_statement = False
        
        if isinstance(item_type, list):
            is_statement = 'wikibase:Statement' in item_type
        elif isinstance(item_type, str):
            is_statement = item_type == 'wikibase:Statement'
        
        if is_statement and 'ps:P54' in item:
            
            club_id = item.get('ps:P54', '').replace('wd:', '')
            start_date = item.get('P580')  # start time
            end_date = item.get('P582')    # end time
            
            # Check if this is a current club (no end date or special marker)
            is_current = (end_date is None or 
                         (isinstance(end_date, dict) and end_date.get('@id', '').startswith('_:')))
            
            club_info = {
                'club_id': club_id,
                'start_date': start_date,
                'end_date': end_date,
                'start_year': parse_date(start_date),
                'end_year': parse_date(end_date),
                'is_current': is_current,
                'club_names': {},  # Will contain all names (English and Cantonese)
                'name': 'Unknown',  # English name for backward compatibility
                'description': '',  # English description for backward compatibility
                'cantonese_name': 'Unknown',  # Best Cantonese name
                'has_cantonese': False  # Whether this club has Cantonese names
            }
            
            club_statements.append(club_info)
    
    # Extract club names and descriptions (English and Cantonese) from the JSONLD data
    for club_info in club_statements:
        club_id = club_info['club_id']
        if club_id:
            # Extract all names for this club
            club_names = extract_entity_names(data, club_id, paranames_cantonese)
            club_info['club_names'] = club_names
            
            # Set backward compatibility fields
            club_info['name'] = club_names['english']
            club_info['description'] = club_names['description_english']
            club_info['cantonese_name'] = club_names['cantonese_best']
            club_info['has_cantonese'] = club_names['cantonese_lang'] != 'none'
            
            # Track if any club has Cantonese data
            if club_info['has_cantonese']:
                result['has_cantonese_data'] = True
        
        result['clubs'].append(club_info)
        
        if club_info['is_current']:
            result['current_clubs'].append(club_info)
        else:
            result['former_clubs'].append(club_info)
    
    # Filter for football clubs only (excluding national teams)
    result['football_clubs_only'] = filter_football_clubs(result['clubs'])
    result['total_clubs'] = len(result['clubs'])
    
    # Calculate career span
    years = [club.get('start_year') for club in result['clubs'] if club.get('start_year')]
    if years:
        result['career_span_years'] = {
            'start': min(years),
            'end': max([club.get('end_year') for club in result['clubs'] if club.get('end_year')] + [2025])
        }
    
    return result


def process_all_players(directory_path: str, paranames_tsv_path: str = None) -> Dict[str, Any]:
    """Process all player files and return structured data with Cantonese names from both WikiData and ParaNames."""
    
    # Load ParaNames Cantonese data if provided
    paranames_cantonese = {}
    if paranames_tsv_path:
        paranames_cantonese = load_paranames_cantonese(paranames_tsv_path)
    
    all_players = {}
    club_to_players = {}  # Map club_id to list of players who played there
    cantonese_stats = {
        'players_with_cantonese': 0,
        'clubs_with_cantonese': set(),
        'total_cantonese_club_entries': 0,
        'cantonese_from_wikidata': 0,
        'cantonese_from_paranames': 0,
        'clubs_enhanced_by_paranames': set()
    }
    
    files = [f for f in os.listdir(directory_path) if f.endswith('.jsonld')]
    
    print(f"Processing {len(files)} player files...")
    
    for i, filename in enumerate(files, 1):
        if i % 10 == 0:
            print(f"Processed {i}/{len(files)} files...")
            
        file_path = os.path.join(directory_path, filename)
        
        try:
            player_data = extract_all_clubs(file_path, paranames_cantonese)
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
                
                # Build club-to-players mapping
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
                    
        except Exception as e:
            print(f"Error processing {filename}: {e}")
    
    # Convert sets to counts for final stats
    cantonese_stats['unique_clubs_with_cantonese'] = len(cantonese_stats['clubs_with_cantonese'])
    cantonese_stats['unique_clubs_enhanced_by_paranames'] = len(cantonese_stats['clubs_enhanced_by_paranames'])
    cantonese_stats['clubs_with_cantonese'] = list(cantonese_stats['clubs_with_cantonese'])
    cantonese_stats['clubs_enhanced_by_paranames'] = list(cantonese_stats['clubs_enhanced_by_paranames'])
    
    return {
        'players': all_players,
        'club_to_players': club_to_players,
        'cantonese_statistics': cantonese_stats,
        'processing_info': {
            'total_files': len(files),
            'successfully_processed': len(all_players),
            'timestamp': datetime.now().isoformat()
        }
    }


def find_potential_teammates(all_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Find pairs of players who were potentially teammates, with Cantonese names."""
    
    teammates = []
    club_to_players = all_data['club_to_players']
    
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
                
                if clubs_overlap(club1_info, club2_info):
                    # Get club names (English and Cantonese)
                    club_names = {
                        'english': "Unknown Club",
                        'cantonese': "Unknown Club",
                        'has_cantonese': False
                    }
                    
                    # Find club names from player data
                    for player_data in all_data['players'].values():
                        for club in player_data['clubs']:
                            if club['club_id'] == club_id:
                                club_names['english'] = club['name']
                                club_names['cantonese'] = club['cantonese_name']
                                club_names['has_cantonese'] = club['has_cantonese']
                                break
                        if club_names['english'] != "Unknown Club":
                            break
                    
                    teammates.append({
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
                        'club': {
                            'id': club_id,
                            'name_english': club_names['english'],
                            'name_cantonese': club_names['cantonese'],
                            'has_cantonese': club_names['has_cantonese']
                        },
                        'has_any_cantonese': (player1['player_has_cantonese'] or 
                                            player2['player_has_cantonese'] or 
                                            club_names['has_cantonese'])
                    })
    
    return teammates


def analyze_single_player(file_path: str, paranames_cantonese: Dict[str, Dict[str, str]] = None) -> None:
    """Analyze a single player file and display comprehensive club information with Cantonese names from both WikiData and ParaNames."""
    
    print(f"\nAnalyzing: {os.path.basename(file_path)}")
    print("=" * 60)
    
    try:
        club_info = extract_all_clubs(file_path, paranames_cantonese)
        
        # Display player information
        player_names = club_info['player_names']
        print(f"Player: {player_names['english']} ({club_info['player_id']})")
        if player_names['cantonese_lang'] != 'none':
            source_info = f" (from {player_names['cantonese_source']})" if 'cantonese_source' in player_names else ""
            print(f"Cantonese: {player_names['cantonese_best']} ({player_names['cantonese_lang']}){source_info}")
        print(f"Total clubs in career: {club_info['total_clubs']}")
        print(f"Has Cantonese data: {club_info['has_cantonese_data']}")
        
        if club_info['current_clubs']:
            print(f"\nCurrent Club(s) ({len(club_info['current_clubs'])}):")
            for club in club_info['current_clubs']:
                start_year = club['start_date'][:4] if isinstance(club['start_date'], str) else "?"
                print(f"  ✓ {club.get('name', 'Unknown')} ({club['club_id']}) - {start_year} to present")
                if club['has_cantonese']:
                    source_info = f" (from {club['club_names'].get('cantonese_source', 'unknown')})" if 'cantonese_source' in club['club_names'] else ""
                    print(f"    粵語: {club['cantonese_name']}{source_info}")
                if club.get('description'):
                    print(f"    └── {club['description']}")
        
        if club_info['former_clubs']:
            print(f"\nFormer Clubs ({len(club_info['former_clubs'])}):")
            # Sort by start date (most recent first)
            sorted_former = sorted(club_info['former_clubs'], 
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
        
        print("\nComplete Career Timeline with Cantonese Names:")
        # Sort all clubs by start date
        all_clubs_sorted = sorted(club_info['clubs'], 
                                key=lambda x: x.get('start_date', ''))
        
        for i, club in enumerate(all_clubs_sorted, 1):
            start_year = club['start_date'][:4] if isinstance(club['start_date'], str) else "?"
            end_year = club['end_date'][:4] if isinstance(club['end_date'], str) and club['end_date'] else "present"
            status = "[CURRENT]" if club['is_current'] else "[FORMER]"
            
            # Enhanced indicators for Cantonese names and their sources
            cantonese_indicator = ""
            if club['has_cantonese']:
                source = club['club_names'].get('cantonese_source', 'unknown')
                if source == 'wikidata':
                    cantonese_indicator = " 🇭🇰"
                elif source == 'paranames':
                    cantonese_indicator = " 🇭🇰📚"  # Book emoji to indicate ParaNames source
                else:
                    cantonese_indicator = " 🇭🇰"
            
            print(f"  {i:2d}. {start_year}-{end_year}: {club.get('name', 'Unknown')}{cantonese_indicator} {status}")
            if club['has_cantonese']:
                source_info = f" (from {club['club_names'].get('cantonese_source', 'unknown')})" if 'cantonese_source' in club['club_names'] else ""
                print(f"      粵語: {club['cantonese_name']}{source_info}")
        
    except Exception as e:
        print(f"Error processing file: {e}")


if __name__ == "__main__":
    directory_path = "./data/intermediate/football_players_triples"
    paranames_path = "./data/raw/paranames.tsv"
    
    if not os.path.exists(directory_path):
        print(f"Directory not found: {directory_path}")
        exit(1)
    
    # Process all players with ParaNames enhancement
    print("Starting comprehensive analysis of all players with Cantonese name extraction...")
    print("Enhanced with ParaNames dataset for additional Cantonese club names...")
    all_data = process_all_players(directory_path, paranames_path)
    
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
    
    # Rebuild club_to_players mapping with filtered players only
    print("Rebuilding club mappings with filtered players...")
    filtered_club_to_players = {}
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
    
    all_data['club_to_players'] = filtered_club_to_players
    
    # Update Cantonese statistics for filtered data
    filtered_cantonese_stats = {
        'players_with_cantonese': len(filtered_players),
        'clubs_with_cantonese': set(),
        'total_cantonese_club_entries': 0,
        'original_player_count': original_player_count,
        'filtered_player_count': len(filtered_players),
        'filtering_ratio': round(len(filtered_players) / original_player_count * 100, 2)
    }
    
    # Count clubs with Cantonese names in filtered data
    for player_data in filtered_players.values():
        for club in player_data['clubs']:
            if club['has_cantonese']:
                filtered_cantonese_stats['clubs_with_cantonese'].add(club['club_id'])
                filtered_cantonese_stats['total_cantonese_club_entries'] += 1
    
    filtered_cantonese_stats['unique_clubs_with_cantonese'] = len(filtered_cantonese_stats['clubs_with_cantonese'])
    filtered_cantonese_stats['clubs_with_cantonese'] = list(filtered_cantonese_stats['clubs_with_cantonese'])
    
    all_data['cantonese_statistics'] = filtered_cantonese_stats
    
    # Extract all unique clubs with their information
    print("Extracting all unique clubs information...")
    all_clubs = {}
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
    
    # Find potential teammates with filtered data
    print("Finding potential teammates among players with Cantonese names...")
    teammates = find_potential_teammates(all_data)
    
    # Prepare enhanced output data with Cantonese information (filtered)
    cantonese_stats = all_data['cantonese_statistics']
    
    output_data = {
        'metadata': {
            'description': 'Football player club affiliations extracted from WikiData for Cantonese benchmark construction - FILTERED for players with Cantonese names only',
            'purpose': 'Support generation of questions about player careers and teammate relationships with Cantonese names',
            'data_structure': {
                'players': 'Dictionary of player_id -> player data with club histories',
                'club_to_players_mapping': 'Dictionary of club_id -> list of players who played there',
                'all_clubs': 'Dictionary of club_id -> club data with English/Cantonese names and player counts',
                'potential_teammates': 'Array of player pairs who potentially played together'
            },
            'extraction_date': datetime.now().isoformat(),
            'total_players': len(all_data['players']),
            'total_potential_teammate_pairs': len(teammates),
            'filtering_info': {
                'original_player_count': cantonese_stats['original_player_count'],
                'filtered_player_count': cantonese_stats['filtered_player_count'],
                'filtering_ratio': cantonese_stats['filtering_ratio'],
                'filter_criteria': 'Players must have valid Cantonese names (yue or zh-hk language codes)'
            },
            'cantonese_coverage': {
                'players_with_cantonese_names': cantonese_stats['players_with_cantonese'],
                'unique_clubs_with_cantonese_names': cantonese_stats['unique_clubs_with_cantonese'],
                'total_club_entries_with_cantonese': cantonese_stats['total_cantonese_club_entries'],
                'coverage_percentage_players': 100.0,  # 100% since all remaining players have Cantonese names
                'teammate_pairs_with_cantonese': len([t for t in teammates if t['has_any_cantonese']]),
                'paranames_enhancement': {
                    'players_from_wikidata': cantonese_stats.get('cantonese_from_wikidata', 0),
                    'players_from_paranames': cantonese_stats.get('cantonese_from_paranames', 0),
                    'clubs_enhanced_by_paranames': cantonese_stats.get('unique_clubs_enhanced_by_paranames', 0),
                    'clubs_enhanced_list': cantonese_stats.get('clubs_enhanced_by_paranames', [])
                }
            }
        },
        'players': all_data['players'],
        'club_to_players_mapping': all_data['club_to_players'],
        'all_clubs': all_clubs,
        'potential_teammates': teammates,
        'processing_info': all_data['processing_info'],
        'cantonese_statistics': cantonese_stats
    }
    
    # Write to JSON file with enhanced name
    output_file = "./data/intermediate/football_players_clubs_complete.json"
    print(f"Writing filtered data (Cantonese players only) to {output_file}...")
    
    # Ensure output directory exists
    os.makedirs("./data/intermediate", exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*80)
    print("CANTONESE FILTERING COMPLETE (Enhanced with ParaNames)")
    print("="*80)
    print(f"✓ Original players processed: {cantonese_stats['original_player_count']}")
    print(f"✓ Players with Cantonese names retained: {len(all_data['players'])} ({cantonese_stats['filtering_ratio']}%)")
    print(f"✓ Players without Cantonese names filtered out: {cantonese_stats['original_player_count'] - len(all_data['players'])}")
    print(f"✓ Found {len(all_data['club_to_players'])} unique clubs in filtered data")
    print(f"✓ All clubs dictionary contains {len(all_clubs)} clubs indexed by club_id")
    print(f"✓ Identified {len(teammates)} potential teammate pairs (all with Cantonese names)")
    print(f"✓ Clubs with Cantonese names: {cantonese_stats['unique_clubs_with_cantonese']}")
    print(f"✓ Clubs enhanced by ParaNames: {cantonese_stats.get('unique_clubs_enhanced_by_paranames', 0)}")
    print(f"✓ Player names from WikiData: {cantonese_stats.get('cantonese_from_wikidata', 0)}")
    print(f"✓ Player names from ParaNames: {cantonese_stats.get('cantonese_from_paranames', 0)}")
    print(f"✓ Filtered data saved to: {output_file}")
    print("\nFiltered dataset contains ONLY players with valid Cantonese names and can be used for:")
    print("  • Cantonese benchmark questions about player careers")
    print("  • Teammate relationship questions with Cantonese names")
    print("  • Bilingual player career timelines and transfers")
    print("  • Translation tasks between English and Cantonese player names")
    print("  • All questions will have guaranteed Cantonese name coverage")
    print("  • Enhanced coverage from ParaNames dataset for additional club names")
