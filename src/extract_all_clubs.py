#!/usr/bin/env python3
"""
Improved script to extract ALL player club information from WikiData JSONLD files.

This version correctly extracts both current and historical clubs by focusing
on the detailed statement objects rather than the simplified P54 property.

Outputs structured data for all players to support Cantonese benchmark construction.
"""

import json
import os
from typing import List, Dict, Any
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
        'football_clubs_only': [],  # Excluding national teams
        'total_clubs': 0,
        'career_span_years': None,
        'file_path': jsonld_file_path
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
                'start_year': parse_date(start_date),
                'end_year': parse_date(end_date),
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
    
    # Combine club info with names and categorize
    for club_info in club_statements:
        club_id = club_info['club_id']
        if club_id in club_names:
            club_info.update(club_names[club_id])
        
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
    """Process all player files and return structured data."""
    
    all_players = {}
    club_to_players = {}  # Map club_id to list of players who played there
    
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
                
                # Build club-to-players mapping
                for club in player_data['clubs']:
                    club_id = club['club_id']
                    if club_id not in club_to_players:
                        club_to_players[club_id] = []
                    
                    club_to_players[club_id].append({
                        'player_id': player_id,
                        'player_name': player_data['player_name'],
                        'start_year': club.get('start_year'),
                        'end_year': club.get('end_year'),
                        'is_current': club['is_current']
                    })
                    
        except Exception as e:
            print(f"Error processing {filename}: {e}")
    
    return {
        'players': all_players,
        'club_to_players': club_to_players,
        'processing_info': {
            'total_files': len(files),
            'successfully_processed': len(all_players),
            'timestamp': datetime.now().isoformat()
        }
    }


def find_potential_teammates(all_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Find pairs of players who were potentially teammates."""
    
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
                    # Get club name
                    club_name = "Unknown Club"
                    if club_id in all_data['players']:
                        for player_data in all_data['players'].values():
                            for club in player_data['clubs']:
                                if club['club_id'] == club_id:
                                    club_name = club['name']
                                    break
                            if club_name != "Unknown Club":
                                break
                    
                    teammates.append({
                        'player1': {
                            'id': player1['player_id'],
                            'name': player1['player_name'],
                            'start_year': player1.get('start_year'),
                            'end_year': player1.get('end_year')
                        },
                        'player2': {
                            'id': player2['player_id'], 
                            'name': player2['player_name'],
                            'start_year': player2.get('start_year'),
                            'end_year': player2.get('end_year')
                        },
                        'club': {
                            'id': club_id,
                            'name': club_name
                        }
                    })
    
    return teammates


def analyze_single_player(file_path: str) -> None:
    """Analyze a single player file and display comprehensive club information."""
    
    print(f"\nAnalyzing: {os.path.basename(file_path)}")
    print("=" * 60)
    
    try:
        club_info = extract_all_clubs(file_path)
        
        print(f"Player: {club_info['player_name']} ({club_info['player_id']})")
        print(f"Total clubs in career: {club_info['total_clubs']}")
        
        if club_info['current_clubs']:
            print(f"\nCurrent Club(s) ({len(club_info['current_clubs'])}):")
            for club in club_info['current_clubs']:
                start_year = club['start_date'][:4] if isinstance(club['start_date'], str) else "?"
                print(f"  ✓ {club.get('name', 'Unknown')} ({club['club_id']}) - {start_year} to present")
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
                if club.get('description'):
                    print(f"    └── {club['description']}")
        
        print("\nComplete Career Timeline:")
        # Sort all clubs by start date
        all_clubs_sorted = sorted(club_info['clubs'], 
                                key=lambda x: x.get('start_date', ''))
        
        for i, club in enumerate(all_clubs_sorted, 1):
            start_year = club['start_date'][:4] if isinstance(club['start_date'], str) else "?"
            end_year = club['end_date'][:4] if isinstance(club['end_date'], str) and club['end_date'] else "present"
            status = "[CURRENT]" if club['is_current'] else "[FORMER]"
            
            print(f"  {i:2d}. {start_year}-{end_year}: {club.get('name', 'Unknown')} {status}")
        
    except Exception as e:
        print(f"Error processing file: {e}")


if __name__ == "__main__":
    directory_path = "/Users/taoyeyao/workplace/CLEVA-Cantonese/data/intermediate/football_players_triples"
    
    if not os.path.exists(directory_path):
        print(f"Directory not found: {directory_path}")
        exit(1)
    
    # Process all players
    print("Starting comprehensive analysis of all players...")
    all_data = process_all_players(directory_path)
    
    # Find potential teammates
    print("Finding potential teammates...")
    teammates = find_potential_teammates(all_data)
    
    # Prepare output data
    output_data = {
        'metadata': {
            'description': 'Football player club affiliations extracted from WikiData for Cantonese benchmark construction',
            'purpose': 'Support generation of questions about player careers and teammate relationships',
            'extraction_date': datetime.now().isoformat(),
            'total_players': len(all_data['players']),
            'total_potential_teammate_pairs': len(teammates)
        },
        'players': all_data['players'],
        'club_to_players_mapping': all_data['club_to_players'],
        'potential_teammates': teammates,
        'processing_info': all_data['processing_info']
    }
    
    # Write to JSON file
    output_file = "/Users/taoyeyao/workplace/CLEVA-Cantonese/data/intermediate/football_players_clubs_complete.json"
    print(f"Writing complete data to {output_file}...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    # Create a summary file for quick reference
    summary_data = {
        'summary': {
            'total_players': len(all_data['players']),
            'total_clubs': len(all_data['club_to_players']),
            'total_teammate_pairs': len(teammates),
            'players_with_multiple_clubs': len([p for p in all_data['players'].values() if len(p['football_clubs_only']) > 1]),
            'extraction_date': datetime.now().isoformat()
        },
        'sample_players': {
            player_id: {
                'name': data['player_name'],
                'total_clubs': data['total_clubs'],
                'football_clubs_count': len(data['football_clubs_only']),
                'current_clubs': [c['name'] for c in data['current_clubs']],
                'career_span': data.get('career_span_years')
            }
            for player_id, data in list(all_data['players'].items())[:10]
        },
        'sample_teammates': teammates[:20]  # First 20 teammate pairs
    }
    
    summary_file = "/Users/taoyeyao/workplace/CLEVA-Cantonese/data/intermediate/football_players_summary.json"
    print(f"Writing summary to {summary_file}...")
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*80)
    print("EXTRACTION COMPLETE")
    print("="*80)
    print(f"✓ Processed {len(all_data['players'])} players")
    print(f"✓ Found {len(all_data['club_to_players'])} unique clubs")
    print(f"✓ Identified {len(teammates)} potential teammate pairs")
    print(f"✓ Complete data: {output_file}")
    print(f"✓ Summary data: {summary_file}")
    print("\nThis data can now be used to generate Cantonese benchmark questions about:")
    print("  • Which teams players have played for")
    print("  • Whether two players have been teammates")
    print("  • Player career timelines and transfers")
    print("  • Club histories and player associations")
