#!/usr/bin/env python3
"""
Utilities for handling Cantonese names and caching.
"""

import json
import os
import csv
from typing import Dict, Any, Optional, Tuple

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

def load_cached_cantonese_names(cache_dir: str) -> Tuple[Optional[Dict], Optional[Dict]]:
    """
    Load cached Cantonese names from the cache directory.
    
    Args:
        cache_dir: Directory containing cached name files
        
    Returns:
        Tuple of (player_names_dict, team_names_dict) or (None, None) if files don't exist
    """
    import os
    
    player_file = os.path.join(cache_dir, 'players_cantonese_names.json')
    team_file = os.path.join(cache_dir, 'teams_cantonese_names.json')
    
    if not os.path.exists(player_file) or not os.path.exists(team_file):
        return None, None
    
    try:
        with open(player_file, 'r', encoding='utf-8') as f:
            player_data = json.load(f)
        
        with open(team_file, 'r', encoding='utf-8') as f:
            team_data = json.load(f)
        
        return player_data['players'], team_data['teams']
    
    except Exception as e:
        print(f"Error loading cached names: {e}")
        return None, None

def get_entity_names_from_cache(entity_id: str, cached_players: Dict = None, cached_teams: Dict = None) -> Optional[Dict[str, Any]]:
    """
    Get entity names from cached data instead of processing JSONLD.
    
    Args:
        entity_id: The entity ID to look up
        cached_players: Cached player names dictionary
        cached_teams: Cached team names dictionary
        
    Returns:
        Entity names dictionary if found, None otherwise
    """
    if cached_players and entity_id in cached_players:
        return cached_players[entity_id]
    
    if cached_teams and entity_id in cached_teams:
        return cached_teams[entity_id]
    
    return None
