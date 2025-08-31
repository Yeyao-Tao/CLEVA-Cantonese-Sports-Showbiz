#!/usr/bin/env python3
"""
Extract player club information from WikiData JSONLD files.

This script demonstrates how to identify a football player's clubs
from WikiData triples stored in JSONLD format.
"""

import json
import os
from typing import List, Dict, Any


def extract_club_info(directory_path: str, filename: str) -> Dict[str, Any]:
    """
    Extract club information for a football player from WikiData JSONLD.
    
    Args:
        jsonld_file_path: Path to the JSONLD file containing player data
        
    Returns:
        Dictionary containing player and club information
    """
    jsonld_file_path = os.path.join(directory_path, filename)
    with open(jsonld_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    result = {
        'player_id': filename.replace('.jsonld', ''),
        'player_name': None,
        'clubs': [],
        'all_club_ids': []
    }
    
    # Extract player information and basic club IDs
    for item in data.get('@graph', []):
        item_id = item.get('@id', '')
        
        # Find main player entity (the Q-number entity)
        if (item_id.startswith('wd:Q') and 
            item.get('@type') == 'wikibase:Item' and 
            not item_id.startswith('wd:P')):  # Skip properties
            
            # Check if this item has P54 (club membership) data
            if 'P54' in item:
                result['player_id'] = item_id.replace('wd:', '')
                
                # Try to get player name from label
                label = item.get('label')
                if isinstance(label, dict) and '@value' in label:
                    result['player_name'] = label['@value']
                elif isinstance(label, list) and len(label) > 0:
                    result['player_name'] = label[0].get('@value', 'Unknown')
                
                # Get basic club IDs from P54 property
                p54_clubs = item.get('P54', [])
                if isinstance(p54_clubs, list):
                    for club_id in p54_clubs:
                        if isinstance(club_id, str) and club_id.startswith('wd:'):
                            result['all_club_ids'].append(club_id.replace('wd:', ''))
                break
    
    # Extract detailed club information with time periods
    club_statements = []
    for item in data.get('@graph', []):
        # Look for P54 statements with detailed information
        if (isinstance(item.get('@type'), list) and 
            'wikibase:Statement' in item.get('@type', []) and 
            'ps:P54' in item):
            
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
                'is_current': is_current
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
    
    # Combine club info with names
    for club_info in club_statements:
        club_id = club_info['club_id']
        if club_id in club_names:
            club_info.update(club_names[club_id])
        
        result['clubs'].append(club_info)
        
    return result


def analyze_clubs_in_directory(directory_path: str) -> None:
    """
    Analyze all JSONLD files in a directory to extract club information.
    
    Args:
        directory_path: Path to directory containing JSONLD files
    """
    print("Football Player Club Analysis")
    print("=" * 50)
    
    files = [f for f in os.listdir(directory_path) if f.endswith('.jsonld')]
    
    for i, filename in enumerate(files[:5]):  # Analyze first 5 files as examples
        file_path = os.path.join(directory_path, filename)
        print(f"\n{i+1}. Analyzing {filename}")
        print("-" * 30)
        
        try:
            club_info = extract_club_info(directory_path, filename)
            print(club_info)
            
            # print(f"Player: {club_info['player_name']} ({club_info['player_id']})")
            
            # if club_info['clubs']:
            #     print(f"All Clubs ({len(club_info['clubs'])} total):")
            #     for club in club_info['clubs']:
            #         status = "Current" if club['is_current'] else "Former"
            #         period = ""
            #         if club['start_date']:
            #             start_year = club['start_date'][:4] if isinstance(club['start_date'], str) else "?"
            #             end_year = club['end_date'][:4] if isinstance(club['end_date'], str) and club['end_date'] else "present"
            #             period = f" ({start_year}-{end_year})"
                    
            #         print(f"  - {club.get('name', 'Unknown')} ({club['club_id']}) - {status}{period}")
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")


if __name__ == "__main__":
    # Example usage with the current workspace
    directory_path = "/Users/taoyeyao/workplace/CLEVA-Cantonese/data/intermediate/football_players_triples"
    
    if os.path.exists(directory_path):
        analyze_clubs_in_directory(directory_path)
        
        # # Detailed analysis of Musiala's file
        # musiala_file = os.path.join(directory_path, "Q96072055.jsonld")
        # if os.path.exists(musiala_file):
        #     print("\n" + "="*50)
        #     print("DETAILED ANALYSIS: Jamal Musiala")
        #     print("="*50)
            
        #     club_info = extract_club_info(musiala_file)
        #     print(f"Player: {club_info['player_name']}")
        #     print(f"WikiData ID: {club_info['player_id']}")
        #     print(f"Total clubs in career: {len(club_info['clubs'])}")
            
        #     print("\nClub History:")
        #     for club in sorted(club_info['clubs'], key=lambda x: x.get('start_date', ''), reverse=True):
        #         start_year = club['start_date'][:4] if isinstance(club['start_date'], str) else "?"
        #         end_year = club['end_date'][:4] if isinstance(club['end_date'], str) and club['end_date'] else "present"
        #         status = "✓ Current" if club['is_current'] else "Former"
                
        #         print(f"  {start_year}-{end_year}: {club.get('name', 'Unknown')} [{status}]")
        #         if club.get('description'):
        #             print(f"    └── {club['description']}")
    else:
        print(f"Directory not found: {directory_path}")
