#!/usr/bin/env python3
"""
Extract and cache all players' and teams' Cantonese names from WikiData JSONLD files.

This script processes all JSONLD files once to extract Cantonese names for players
and teams, then stores them in cached mapping files. This avoids repeated lookups
in other scripts, significantly improving performance.
"""

import json
import os
from typing import Dict, Any, Set
from datetime import datetime
import sys

# Add the src directory to Python path to import utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.jsonld_reader import (
    extract_entity_names,
    load_jsonld_file
)
from utils.cantonese_utils import (
    load_paranames_cantonese,
    load_cached_cantonese_names
)
from utils.file_utils import (
    extract_player_id_from_filename,
    get_all_jsonld_files
)


def extract_all_entity_ids_from_jsonld(jsonld_file_path: str) -> Set[str]:
    """
    Extract all entity IDs mentioned in a JSONLD file (players and teams).
    
    Args:
        jsonld_file_path: Path to the JSONLD file
        
    Returns:
        Set of entity IDs found in the file
    """
    try:
        data = load_jsonld_file(jsonld_file_path)
    except Exception as e:
        print(f"Error loading {jsonld_file_path}: {e}")
        return set()
    
    entity_ids = set()
    
    # Get player ID from filename
    player_id = extract_player_id_from_filename(jsonld_file_path)
    if player_id:
        entity_ids.add(player_id)
    
    # Extract team/club IDs from P54 statements (member of sports team)
    for item in data.get('@graph', []):
        item_type = item.get('@type')
        is_statement = False
        
        if isinstance(item_type, list):
            is_statement = 'wikibase:Statement' in item_type
        elif isinstance(item_type, str):
            is_statement = item_type == 'wikibase:Statement'
        
        if is_statement and 'ps:P54' in item:
            team_id = item.get('ps:P54', '').replace('wd:', '')
            if team_id:
                entity_ids.add(team_id)
    
    return entity_ids


def extract_all_cantonese_names(directory_path: str, paranames_tsv_path: str = None) -> Dict[str, Any]:
    """
    Extract Cantonese names for all entities found in JSONLD files.
    
    Args:
        directory_path: Path to directory containing JSONLD files
        paranames_tsv_path: Path to ParaNames TSV file (optional)
        
    Returns:
        Dictionary containing all entity names and metadata
    """
    # Load ParaNames Cantonese data if provided
    paranames_cantonese = {}
    if paranames_tsv_path:
        paranames_cantonese = load_paranames_cantonese(paranames_tsv_path)
    
    # Get all JSONLD files
    jsonld_files = get_all_jsonld_files(directory_path)
    
    if not jsonld_files:
        return {
            'players': {},
            'teams': {},
            'error': f"No JSONLD files found in directory: {directory_path}"
        }
    
    print(f"Processing {len(jsonld_files)} JSONLD files to extract entity IDs...")
    
    # First pass: collect all unique entity IDs
    all_entity_ids = set()
    player_ids = set()
    
    for i, file_path in enumerate(jsonld_files, 1):
        if i % 50 == 0:
            print(f"Processed {i}/{len(jsonld_files)} files for entity ID extraction...")
        
        entity_ids = extract_all_entity_ids_from_jsonld(file_path)
        all_entity_ids.update(entity_ids)
        
        # Track player IDs separately
        player_id = extract_player_id_from_filename(file_path)
        if player_id:
            player_ids.add(player_id)
    
    team_ids = all_entity_ids - player_ids
    
    print(f"Found {len(player_ids)} unique players and {len(team_ids)} unique teams/clubs")
    print(f"Total unique entities: {len(all_entity_ids)}")
    
    # Second pass: extract names for all entities
    print("Extracting Cantonese names for all entities...")
    
    player_names = {}
    team_names = {}
    processed_entities = set()
    
    for i, file_path in enumerate(jsonld_files, 1):
        if i % 20 == 0:
            print(f"Processed {i}/{len(jsonld_files)} files for name extraction...")
        
        try:
            data = load_jsonld_file(file_path)
            
            # Extract names for all entities found in this file
            file_entity_ids = extract_all_entity_ids_from_jsonld(file_path)
            
            for entity_id in file_entity_ids:
                if entity_id in processed_entities:
                    continue  # Already processed this entity
                
                entity_names = extract_entity_names(data, entity_id, paranames_cantonese)
                
                if entity_id in player_ids:
                    player_names[entity_id] = entity_names
                else:
                    team_names[entity_id] = entity_names
                
                processed_entities.add(entity_id)
        
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue
    
    # Fill in any missing entities (entities that were referenced but not fully detailed in processed files)
    missing_entities = all_entity_ids - processed_entities
    if missing_entities:
        print(f"Processing {len(missing_entities)} entities that were referenced but not detailed...")
        
        # For missing entities, try to find them in any file where they might be detailed
        for entity_id in missing_entities:
            found = False
            for file_path in jsonld_files:
                try:
                    data = load_jsonld_file(file_path)
                    
                    # Check if this entity is detailed in this file
                    entity_names = extract_entity_names(data, entity_id, paranames_cantonese)
                    if entity_names['english'] != 'Unknown':  # Found detailed information
                        if entity_id in player_ids:
                            player_names[entity_id] = entity_names
                        else:
                            team_names[entity_id] = entity_names
                        found = True
                        break
                
                except Exception:
                    continue
            
            if not found:
                # Create minimal entry for unknown entities
                minimal_names = {
                    'id': entity_id,
                    'english': 'Unknown',
                    'cantonese': {},
                    'cantonese_best': 'Unknown',
                    'cantonese_lang': 'none',
                    'description_english': '',
                    'description_cantonese': {},
                    'cantonese_source': 'none'
                }
                
                if entity_id in player_ids:
                    player_names[entity_id] = minimal_names
                else:
                    team_names[entity_id] = minimal_names
    
    # Calculate statistics
    players_with_cantonese = sum(1 for names in player_names.values() if names['cantonese_lang'] != 'none')
    teams_with_cantonese = sum(1 for names in team_names.values() if names['cantonese_lang'] != 'none')
    
    players_from_wikidata = sum(1 for names in player_names.values() if names['cantonese_source'] == 'wikidata')
    players_from_paranames = sum(1 for names in player_names.values() if names['cantonese_source'] == 'paranames')
    
    teams_from_wikidata = sum(1 for names in team_names.values() if names['cantonese_source'] == 'wikidata')
    teams_from_paranames = sum(1 for names in team_names.values() if names['cantonese_source'] == 'paranames')
    
    return {
        'players': player_names,
        'teams': team_names,
        'statistics': {
            'total_players': len(player_names),
            'total_teams': len(team_names),
            'players_with_cantonese': players_with_cantonese,
            'teams_with_cantonese': teams_with_cantonese,
            'players_cantonese_percentage': round(players_with_cantonese / len(player_names) * 100, 2) if player_names else 0,
            'teams_cantonese_percentage': round(teams_with_cantonese / len(team_names) * 100, 2) if team_names else 0,
            'players_from_wikidata': players_from_wikidata,
            'players_from_paranames': players_from_paranames,
            'teams_from_wikidata': teams_from_wikidata,
            'teams_from_paranames': teams_from_paranames
        },
        'processing_info': {
            'timestamp': datetime.now().isoformat(),
            'directory_processed': directory_path,
            'paranames_file_used': paranames_tsv_path if paranames_tsv_path else None,
            'jsonld_files_processed': len(jsonld_files)
        }
    }


def save_cantonese_mappings(data: Dict[str, Any], output_dir: str):
    """
    Save the Cantonese name mappings to separate files.
    
    Args:
        data: The extracted data containing players and teams
        output_dir: Directory to save the mapping files
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Save player names
    player_output = {
        'metadata': {
            'description': 'Cached Cantonese names for football players extracted from WikiData',
            'purpose': 'Avoid repeated name lookups in other scripts',
            'total_players': len(data['players']),
            'players_with_cantonese': data['statistics']['players_with_cantonese'],
            'cantonese_coverage_percentage': data['statistics']['players_cantonese_percentage'],
            'extraction_date': data['processing_info']['timestamp'],
            'sources': ['WikiData JSONLD', 'ParaNames dataset'] if data['processing_info']['paranames_file_used'] else ['WikiData JSONLD']
        },
        'players': data['players']
    }
    
    player_file = os.path.join(output_dir, 'players_cantonese_names.json')
    with open(player_file, 'w', encoding='utf-8') as f:
        json.dump(player_output, f, indent=2, ensure_ascii=False)
    
    # Save team names
    team_output = {
        'metadata': {
            'description': 'Cached Cantonese names for football teams/clubs extracted from WikiData',
            'purpose': 'Avoid repeated name lookups in other scripts',
            'total_teams': len(data['teams']),
            'teams_with_cantonese': data['statistics']['teams_with_cantonese'],
            'cantonese_coverage_percentage': data['statistics']['teams_cantonese_percentage'],
            'extraction_date': data['processing_info']['timestamp'],
            'sources': ['WikiData JSONLD', 'ParaNames dataset'] if data['processing_info']['paranames_file_used'] else ['WikiData JSONLD']
        },
        'teams': data['teams']
    }
    
    team_file = os.path.join(output_dir, 'teams_cantonese_names.json')
    with open(team_file, 'w', encoding='utf-8') as f:
        json.dump(team_output, f, indent=2, ensure_ascii=False)
    
    # Save combined statistics
    stats_output = {
        'metadata': {
            'description': 'Statistics about Cantonese name extraction from WikiData',
            'extraction_date': data['processing_info']['timestamp']
        },
        'statistics': data['statistics'],
        'processing_info': data['processing_info']
    }
    
    stats_file = os.path.join(output_dir, 'cantonese_extraction_stats.json')
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats_output, f, indent=2, ensure_ascii=False)
    
    return player_file, team_file, stats_file


if __name__ == "__main__":
    # Configuration
    directory_path = "./data/intermediate/football_players_triples"
    paranames_path = "./data/raw/paranames.tsv"
    output_dir = "./data/cantonese_name_mapping"
    
    # Check if directory exists
    if not os.path.exists(directory_path):
        print(f"Directory not found: {directory_path}")
        exit(1)
    
    # Extract all Cantonese names
    print("Starting comprehensive Cantonese name extraction...")
    print("This will process all JSONLD files and create cached name mappings...")
    all_data = extract_all_cantonese_names(directory_path, paranames_path)
    
    if 'error' in all_data:
        print(f"Error: {all_data['error']}")
        exit(1)
    
    # Save the mappings
    print("Saving Cantonese name mappings...")
    player_file, team_file, stats_file = save_cantonese_mappings(all_data, output_dir)
    
    # Display results
    stats = all_data['statistics']
    
    print("\n" + "="*80)
    print("CANTONESE NAME EXTRACTION COMPLETE")
    print("="*80)
    
    print(f"✓ Total players processed: {stats['total_players']}")
    print(f"✓ Players with Cantonese names: {stats['players_with_cantonese']} ({stats['players_cantonese_percentage']}%)")
    print(f"✓ Total teams/clubs processed: {stats['total_teams']}")
    print(f"✓ Teams with Cantonese names: {stats['teams_with_cantonese']} ({stats['teams_cantonese_percentage']}%)")
    
    print(f"\n✓ Player names saved to: {player_file}")
    print(f"✓ Team names saved to: {team_file}")
    print(f"✓ Statistics saved to: {stats_file}")
    
    print(f"\nSource breakdown:")
    print(f"  • Players from WikiData: {stats['players_from_wikidata']}")
    print(f"  • Players from ParaNames: {stats['players_from_paranames']}")
    print(f"  • Teams from WikiData: {stats['teams_from_wikidata']}")
    print(f"  • Teams from ParaNames: {stats['teams_from_paranames']}")
    
    print(f"\nCached files can now be used by other scripts to avoid repeated name lookups!")
    print(f"Use load_cached_cantonese_names('{output_dir}') to load the cached data.")
