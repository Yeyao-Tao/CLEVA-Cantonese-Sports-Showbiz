#!/usr/bin/env python3
"""
Extract player birth years from WikiData JSONLD files.

This script reads a directory of players' JSONLD files, extracts birth year information,
and stores the results in a structured output file. It uses the shared utilities
from the utils module to avoid code duplication.
"""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
import sys

# Add the src directory to Python path to import utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.jsonld_reader import (
    extract_entity_names,
    load_jsonld_file,
    extract_property_value
)
from utils.cantonese_utils import (
    load_paranames_cantonese,
    load_cached_cantonese_names,
    get_entity_names_from_cache
)
from utils.date_utils import parse_date
from utils.file_utils import (
    extract_player_id_from_filename,
    get_all_jsonld_files
)


def extract_birth_year(jsonld_file_path: str, cached_players: Dict = None) -> Dict[str, Any]:
    """
    Extract birth year information for a football player from WikiData JSONLD.
    
    Args:
        jsonld_file_path: Path to the JSONLD file containing player data
        cached_players: Dictionary of cached player names
        
    Returns:
        Dictionary containing player information and birth year
    """
    try:
        data = load_jsonld_file(jsonld_file_path)
    except Exception as e:
        return {
            'error': f"Failed to load JSONLD file: {e}",
            'file_path': jsonld_file_path
        }
    
    result = {
        'player_id': None,
        'player_names': {},
        'birth_date': None,
        'birth_year': None,
        'file_path': jsonld_file_path,
        'has_cantonese_data': False,
        'has_birth_data': False
    }
    
    # Extract player ID from filename
    player_id = extract_player_id_from_filename(jsonld_file_path)
    if not player_id:
        result['error'] = "Invalid filename format"
        return result
    
    result['player_id'] = player_id
    
    # Get player names from cache if available, otherwise use fallback
    if cached_players:
        cached_names = get_entity_names_from_cache(player_id, cached_players)
        if cached_names:
            result['player_names'] = cached_names
        else:
            # Fallback: basic name extraction if not in cache
            result['player_names'] = {
                'id': player_id,
                'english': 'Unknown',
                'cantonese': {},
                'cantonese_best': 'Unknown',
                'cantonese_lang': 'none',
                'description_english': '',
                'description_cantonese': {},
                'cantonese_source': 'none'
            }
    else:
        # No cache available, use basic extraction
        result['player_names'] = {
            'id': player_id,
            'english': 'Unknown',
            'cantonese': {},
            'cantonese_best': 'Unknown',
            'cantonese_lang': 'none',
            'description_english': '',
            'description_cantonese': {},
            'cantonese_source': 'none'
        }
    
    # Check if we have Cantonese data for the player
    if result['player_names']['cantonese_lang'] != 'none':
        result['has_cantonese_data'] = True
    
    # Extract birth date using P569 property (date of birth)
    birth_date = extract_property_value(data, player_id, 'P569')
    
    if birth_date:
        result['birth_date'] = birth_date
        result['birth_year'] = parse_date(birth_date)
        result['has_birth_data'] = True
    
    return result


def process_all_players_birth_years(directory_path: str, cache_dir: str = None) -> Dict[str, Any]:
    """
    Process all player files and extract birth year information.
    
    Args:
        directory_path: Path to directory containing JSONLD files
        cache_dir: Path to directory containing cached Cantonese names
        
    Returns:
        Dictionary containing all player birth year data with statistics
    """
    # Load cached Cantonese names if available
    cached_players = None
    cache_info = "No cache used"
    
    if cache_dir and os.path.exists(cache_dir):
        print(f"Loading cached Cantonese names from {cache_dir}...")
        cached_players, _ = load_cached_cantonese_names(cache_dir)
        if cached_players:
            cache_info = f"Using cached names for {len(cached_players)} players"
            print(cache_info)
        else:
            print("Failed to load cached names, proceeding without cache")
    else:
        print("No cache directory provided or cache directory not found, proceeding without cache")
    
    all_players = {}
    statistics = {
        'total_files_processed': 0,
        'players_with_birth_data': 0,
        'players_with_cantonese_data': 0,
        'players_with_both_birth_and_cantonese': 0,
        'birth_year_range': {'min': None, 'max': None},
        'birth_years_distribution': {},
        'errors': [],
        'cache_info': cache_info
    }
    
    # Get all JSONLD files
    jsonld_files = get_all_jsonld_files(directory_path)
    
    if not jsonld_files:
        return {
            'players': {},
            'statistics': statistics,
            'error': f"No JSONLD files found in directory: {directory_path}"
        }
    
    print(f"Processing {len(jsonld_files)} player files for birth year extraction...")
    
    for i, file_path in enumerate(jsonld_files, 1):
        if i % 50 == 0:
            print(f"Processed {i}/{len(jsonld_files)} files...")
        
        try:
            player_data = extract_birth_year(file_path, cached_players)
            statistics['total_files_processed'] += 1
            
            if 'error' in player_data:
                statistics['errors'].append({
                    'file': file_path,
                    'error': player_data['error']
                })
                continue
            
            player_id = player_data['player_id']
            if player_id:
                all_players[player_id] = player_data
                
                # Update statistics
                if player_data['has_birth_data']:
                    statistics['players_with_birth_data'] += 1
                    
                    birth_year = player_data['birth_year']
                    if birth_year:
                        # Update birth year range
                        if statistics['birth_year_range']['min'] is None or birth_year < statistics['birth_year_range']['min']:
                            statistics['birth_year_range']['min'] = birth_year
                        if statistics['birth_year_range']['max'] is None or birth_year > statistics['birth_year_range']['max']:
                            statistics['birth_year_range']['max'] = birth_year
                        
                        # Update birth year distribution
                        if birth_year not in statistics['birth_years_distribution']:
                            statistics['birth_years_distribution'][birth_year] = 0
                        statistics['birth_years_distribution'][birth_year] += 1
                
                if player_data['has_cantonese_data']:
                    statistics['players_with_cantonese_data'] += 1
                
                if player_data['has_birth_data'] and player_data['has_cantonese_data']:
                    statistics['players_with_both_birth_and_cantonese'] += 1
                    
        except Exception as e:
            statistics['errors'].append({
                'file': file_path,
                'error': str(e)
            })
    
    # Calculate additional statistics
    statistics['successfully_processed'] = len(all_players)
    statistics['birth_data_coverage_percentage'] = round(
        (statistics['players_with_birth_data'] / statistics['successfully_processed'] * 100) 
        if statistics['successfully_processed'] > 0 else 0, 2
    )
    statistics['cantonese_data_coverage_percentage'] = round(
        (statistics['players_with_cantonese_data'] / statistics['successfully_processed'] * 100) 
        if statistics['successfully_processed'] > 0 else 0, 2
    )
    statistics['both_data_coverage_percentage'] = round(
        (statistics['players_with_both_birth_and_cantonese'] / statistics['successfully_processed'] * 100) 
        if statistics['successfully_processed'] > 0 else 0, 2
    )
    
    return {
        'players': all_players,
        'statistics': statistics,
        'processing_info': {
            'timestamp': datetime.now().isoformat(),
            'directory_processed': directory_path,
            'cache_directory_used': cache_dir if cache_dir else None,
            'cache_status': cache_info
        }
    }


def filter_players_with_birth_data(all_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter to keep only players with valid birth year data.
    
    Args:
        all_data: Full dataset with all players
        
    Returns:
        Filtered dataset containing only players with birth data
    """
    original_count = len(all_data['players'])
    
    filtered_players = {
        player_id: player_data 
        for player_id, player_data in all_data['players'].items() 
        if player_data['has_birth_data']
    }
    
    filtered_count = len(filtered_players)
    
    # Update the dataset
    all_data['players'] = filtered_players
    
    # Update statistics for filtered data
    all_data['statistics']['original_player_count'] = original_count
    all_data['statistics']['filtered_player_count'] = filtered_count
    all_data['statistics']['filtering_ratio'] = round(
        (filtered_count / original_count * 100) if original_count > 0 else 0, 2
    )
    
    return all_data


def analyze_birth_years(all_data: Dict[str, Any]) -> None:
    """
    Print detailed analysis of birth year data.
    
    Args:
        all_data: Dataset containing player birth year information
    """
    stats = all_data['statistics']
    players = all_data['players']
    
    print("\n" + "="*80)
    print("BIRTH YEAR EXTRACTION ANALYSIS")
    print("="*80)
    
    print(f"Total files processed: {stats['total_files_processed']}")
    print(f"Successfully processed players: {stats['successfully_processed']}")
    print(f"Players with birth data: {stats['players_with_birth_data']} ({stats['birth_data_coverage_percentage']}%)")
    print(f"Players with Cantonese data: {stats['players_with_cantonese_data']} ({stats['cantonese_data_coverage_percentage']}%)")
    print(f"Players with both birth and Cantonese data: {stats['players_with_both_birth_and_cantonese']} ({stats['both_data_coverage_percentage']}%)")
    
    if stats['birth_year_range']['min'] and stats['birth_year_range']['max']:
        print(f"Birth year range: {stats['birth_year_range']['min']} - {stats['birth_year_range']['max']}")
    
    if stats['errors']:
        print(f"\nErrors encountered: {len(stats['errors'])}")
        for error in stats['errors'][:5]:  # Show first 5 errors
            print(f"  - {os.path.basename(error['file'])}: {error['error']}")
        if len(stats['errors']) > 5:
            print(f"  ... and {len(stats['errors']) - 5} more errors")
    
    # Show birth year distribution (top 10 years)
    if stats['birth_years_distribution']:
        print(f"\nTop 10 birth years by frequency:")
        sorted_years = sorted(stats['birth_years_distribution'].items(), 
                            key=lambda x: x[1], reverse=True)[:10]
        for year, count in sorted_years:
            print(f"  {year}: {count} players")
    
    # Show some example players with both birth and Cantonese data
    players_with_both = [
        (player_id, player_data) 
        for player_id, player_data in players.items() 
        if player_data['has_birth_data'] and player_data['has_cantonese_data']
    ]
    
    if players_with_both:
        print(f"\nSample players with both birth year and Cantonese data:")
        for player_id, player_data in players_with_both[:5]:
            names = player_data['player_names']
            print(f"  {names['english']} ({names['cantonese_best']}) - Born: {player_data['birth_year']}")


if __name__ == "__main__":
    import time
    
    # Configuration
    directory_path = "./data/soccer/intermediate/football_players_triples"
    cache_dir = "./data/soccer/cantonese_name_mapping"
    output_file = "./data/soccer/intermediate/players_birth_years.json"
    
    # Check if directory exists
    if not os.path.exists(directory_path):
        print(f"Directory not found: {directory_path}")
        exit(1)
    
    # Measure performance
    start_time = time.time()
    
    # Process all players to extract birth years
    print("Starting birth year extraction for all players...")
    print("Using cached Cantonese names for improved performance...")
    all_data = process_all_players_birth_years(directory_path, cache_dir)
    
    # Filter to keep only players with birth data
    print("Filtering players to keep only those with birth year data...")
    filtered_data = filter_players_with_birth_data(all_data)
    
    processing_time = time.time() - start_time
    
    # Prepare output data with metadata
    output_data = {
        'metadata': {
            'description': 'Football player birth years extracted from WikiData for analysis and benchmark construction',
            'purpose': 'Support generation of questions about player ages, birth years, and generational analysis',
            'data_structure': {
                'players': 'Dictionary of player_id -> player data with birth year information',
                'note': 'Only includes players with valid birth year data'
            },
            'extraction_date': datetime.now().isoformat(),
            'total_players_with_birth_data': len(filtered_data['players']),
            'processing_time_seconds': round(processing_time, 2),
            'performance_optimization': 'Uses cached Cantonese names for improved speed',
            'filtering_info': {
                'original_player_count': filtered_data['statistics']['original_player_count'],
                'filtered_player_count': filtered_data['statistics']['filtered_player_count'],
                'filtering_ratio': filtered_data['statistics']['filtering_ratio'],
                'filter_criteria': 'Players must have valid birth year data (P569 property)'
            }
        },
        'players': filtered_data['players'],
        'statistics': filtered_data['statistics'],
        'processing_info': filtered_data['processing_info']
    }
    
    # Write to JSON file
    print(f"Writing birth year data to {output_file}...")
    
    # Ensure output directory exists
    os.makedirs("./data/soccer/intermediate", exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    # Show analysis
    analyze_birth_years(filtered_data)
    
    print(f"\n✓ Birth year data saved to: {output_file}")
    print(f"✓ Processing time: {processing_time:.2f} seconds")
    print(f"✓ Cache status: {filtered_data['statistics']['cache_info']}")
    print("\nFiltered dataset contains ONLY players with valid birth year data and can be used for:")
    print("  • Age-related questions and analysis")
    print("  • Birth year and generational comparisons")
    print("  • Player career timeline analysis with age context")
    print("  • Questions about youngest/oldest players")
    print("  • Bilingual questions combining player names and birth information")
