#!/usr/bin/env python3
"""
Improved script to extract ALL player club information from WikiData JSONLD files.

This version correctly extracts both current and historical clubs by focusing
on the detailed statement objects rather than the simplified P54 property.

Outputs structured data for all players to support Cantonese benchmark construction.
"""

import json
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime


def parse_date(date_str):
    """Parse WikiData date string to extract year."""
    if isinstance(date_str, str) and len(date_str) >= 4:
        return int(date_str[:4])
    return None


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


def get_best_cantonese_name(cantonese_labels: Dict[str, str], fallback_name: str = 'Unknown') -> Tuple[str, str]:
    """
    Get the best Cantonese name from available labels.
    Prioritizes 'yue' over 'zh-hk', returns language code used.
    
    Args:
        cantonese_labels: Dict of language codes to labels
        fallback_name: Name to use if no Cantonese labels found
        
    Returns:
        Tuple of (best_name, language_code_used)
    """
    if 'yue' in cantonese_labels:
        return cantonese_labels['yue'], 'yue'
    elif 'zh-hk' in cantonese_labels:
        return cantonese_labels['zh-hk'], 'zh-hk'
    else:
        return fallback_name, 'none'


def extract_entity_names(data: dict, target_id: str) -> Dict[str, Any]:
    """
    Extract all available names for an entity (English, Cantonese, etc.).
    
    Args:
        data: The parsed JSON-LD data
        target_id: The entity ID to extract names for
        
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
        'description_cantonese': {}
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
    
    # Set best Cantonese name
    names['cantonese_best'], names['cantonese_lang'] = get_best_cantonese_name(
        names['cantonese'], names['english']
    )
    
    return names
    """
    Extract ALL club information for a football player from WikiData JSONLD.
    
    Args:
        jsonld_file_path: Path to the JSONLD file containing player data
        
    Returns:
        Dictionary containing complete player and club information
    """
    with open(jsonld_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    result = {
        'player_id': None,
        'player_name': None,
        'clubs': [],
        'current_clubs': [],
        'former_clubs': [],
        'total_clubs': 0
    }
    
    # Extract player ID from filename
    filename = os.path.basename(jsonld_file_path)
    if filename.startswith('Q') and filename.endswith('.jsonld'):
        result['player_id'] = filename[:-7]  # Remove .jsonld extension
    
    # Extract player name from Wikipedia entries
    for item in data.get('@graph', []):
        if (item.get('@type') == 'schema:Article' and 
            'name' in item and 
            item.get('inLanguage') == 'en' and
            'wikipedia.org' in item.get('@id', '')):
            
            name = item.get('name', {})
            if isinstance(name, dict) and '@value' in name:
                result['player_name'] = name['@value']
                break
    
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
                'is_current': is_current,
                'name': 'Unknown',
                'description': ''
            }
            
            club_statements.append(club_info)
    
    # Get club names and descriptions from the JSONLD data
    club_names = {}
    for item in data.get('@graph', []):
        item_id = item.get('@id', '')
        if (item.get('@type') == 'wikibase:Item' and 
            item_id.startswith('wd:Q') and 
            'label' in item):
            
            club_id = item_id.replace('wd:', '')
            
            # Handle label (can be dict or list)
            label = item.get('label')
            club_name = 'Unknown'
            if isinstance(label, dict) and '@value' in label:
                club_name = label['@value']
            elif isinstance(label, list) and len(label) > 0 and '@value' in label[0]:
                club_name = label[0]['@value']
            
            # Handle description (can be dict or list)
            description = item.get('description', '')
            club_description = ''
            if isinstance(description, dict) and '@value' in description:
                club_description = description['@value']
            elif isinstance(description, list) and len(description) > 0 and '@value' in description[0]:
                club_description = description[0]['@value']
            
            club_names[club_id] = {
                'name': club_name,
                'description': club_description
            }
    
def extract_all_clubs(jsonld_file_path: str) -> Dict[str, Any]:
    """
    Extract ALL club information for a football player from WikiData JSONLD.
    Now includes Cantonese names for both players and clubs.
    
    Args:
        jsonld_file_path: Path to the JSONLD file containing player data
        
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
        result['player_names'] = extract_entity_names(data, player_id)
        
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
            club_names = extract_entity_names(data, club_id)
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


def process_all_players(directory_path: str) -> Dict[str, Any]:
    """Process all player files and return structured data with Cantonese names."""
    
    all_players = {}
    club_to_players = {}  # Map club_id to list of players who played there
    cantonese_stats = {
        'players_with_cantonese': 0,
        'clubs_with_cantonese': set(),
        'total_cantonese_club_entries': 0
    }
    
    files = [f for f in os.listdir(directory_path) if f.endswith('.jsonld')]
    
    print(f"Processing {len(files)} player files...")
    
    for i, filename in enumerate(files, 1):
        if i % 10 == 0:
            print(f"Processed {i}/{len(files)} files...")
            
        file_path = os.path.join(directory_path, filename)
        
        try:
            player_data = extract_all_clubs(file_path)
            player_id = player_data['player_id']
            
            if player_id:
                all_players[player_id] = player_data
                
                # Track Cantonese statistics
                if player_data['has_cantonese_data']:
                    cantonese_stats['players_with_cantonese'] += 1
                
                # Build club-to-players mapping
                for club in player_data['clubs']:
                    club_id = club['club_id']
                    if club_id not in club_to_players:
                        club_to_players[club_id] = []
                    
                    # Track clubs with Cantonese names
                    if club['has_cantonese']:
                        cantonese_stats['clubs_with_cantonese'].add(club_id)
                        cantonese_stats['total_cantonese_club_entries'] += 1
                    
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
    
    # Convert set to count for final stats
    cantonese_stats['unique_clubs_with_cantonese'] = len(cantonese_stats['clubs_with_cantonese'])
    cantonese_stats['clubs_with_cantonese'] = list(cantonese_stats['clubs_with_cantonese'])
    
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


def analyze_single_player(file_path: str) -> None:
    """Analyze a single player file and display comprehensive club information with Cantonese names."""
    
    print(f"\nAnalyzing: {os.path.basename(file_path)}")
    print("=" * 60)
    
    try:
        club_info = extract_all_clubs(file_path)
        
        # Display player information
        player_names = club_info['player_names']
        print(f"Player: {player_names['english']} ({club_info['player_id']})")
        if player_names['cantonese_lang'] != 'none':
            print(f"Cantonese: {player_names['cantonese_best']} ({player_names['cantonese_lang']})")
        print(f"Total clubs in career: {club_info['total_clubs']}")
        print(f"Has Cantonese data: {club_info['has_cantonese_data']}")
        
        if club_info['current_clubs']:
            print(f"\nCurrent Club(s) ({len(club_info['current_clubs'])}):")
            for club in club_info['current_clubs']:
                start_year = club['start_date'][:4] if isinstance(club['start_date'], str) else "?"
                print(f"  ✓ {club.get('name', 'Unknown')} ({club['club_id']}) - {start_year} to present")
                if club['has_cantonese']:
                    print(f"    粵語: {club['cantonese_name']}")
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
                    print(f"    粵語: {club['cantonese_name']}")
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
            cantonese_indicator = " 🇭🇰" if club['has_cantonese'] else ""
            
            print(f"  {i:2d}. {start_year}-{end_year}: {club.get('name', 'Unknown')}{cantonese_indicator} {status}")
            if club['has_cantonese']:
                print(f"      粵語: {club['cantonese_name']}")
        
    except Exception as e:
        print(f"Error processing file: {e}")


if __name__ == "__main__":
    directory_path = "./data/intermediate/football_players_triples"
    
    if not os.path.exists(directory_path):
        print(f"Directory not found: {directory_path}")
        exit(1)
    
    # Process all players
    print("Starting comprehensive analysis of all players with Cantonese name extraction...")
    all_data = process_all_players(directory_path)
    
    # Find potential teammates
    print("Finding potential teammates...")
    teammates = find_potential_teammates(all_data)
    
    # Prepare enhanced output data with Cantonese information
    cantonese_stats = all_data['cantonese_statistics']
    
    output_data = {
        'metadata': {
            'description': 'Football player club affiliations extracted from WikiData for Cantonese benchmark construction',
            'purpose': 'Support generation of questions about player careers and teammate relationships with Cantonese names',
            'extraction_date': datetime.now().isoformat(),
            'total_players': len(all_data['players']),
            'total_potential_teammate_pairs': len(teammates),
            'cantonese_coverage': {
                'players_with_cantonese_names': cantonese_stats['players_with_cantonese'],
                'unique_clubs_with_cantonese_names': cantonese_stats['unique_clubs_with_cantonese'],
                'total_club_entries_with_cantonese': cantonese_stats['total_cantonese_club_entries'],
                'coverage_percentage_players': round(cantonese_stats['players_with_cantonese'] / len(all_data['players']) * 100, 2),
                'teammate_pairs_with_cantonese': len([t for t in teammates if t['has_any_cantonese']])
            }
        },
        'players': all_data['players'],
        'club_to_players_mapping': all_data['club_to_players'],
        'potential_teammates': teammates,
        'processing_info': all_data['processing_info'],
        'cantonese_statistics': cantonese_stats
    }
    
    # Write to JSON file with enhanced name
    output_file = "./data/intermediate/football_players_clubs_complete.json"
    print(f"Writing complete data with Cantonese names to {output_file}...")
    
    # Ensure output directory exists
    os.makedirs("./data/intermediate", exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*80)
    print("CANTONESE EXTRACTION COMPLETE")
    print("="*80)
    print(f"✓ Processed {len(all_data['players'])} players")
    print(f"✓ Found {len(all_data['club_to_players'])} unique clubs")
    print(f"✓ Identified {len(teammates)} potential teammate pairs")
    print(f"✓ Players with Cantonese names: {cantonese_stats['players_with_cantonese']} ({output_data['metadata']['cantonese_coverage']['coverage_percentage_players']}%)")
    print(f"✓ Clubs with Cantonese names: {cantonese_stats['unique_clubs_with_cantonese']}")
    print(f"✓ Teammate pairs with Cantonese data: {output_data['metadata']['cantonese_coverage']['teammate_pairs_with_cantonese']}")
    print(f"✓ Complete data with Cantonese: {output_file}")
    print("\nThis enhanced data can now be used to generate Cantonese benchmark questions about:")
    print("  • Which teams players have played for (in Cantonese)")
    print("  • Whether two players have been teammates (with Cantonese names)")
    print("  • Player career timelines and transfers (bilingual)")
    print("  • Club histories and player associations (with Cantonese club names)")
    print("  • Translation tasks between English and Cantonese football names")
