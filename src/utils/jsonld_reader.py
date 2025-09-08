#!/usr/bin/env python3
"""
Common utilities for reading and parsing WikiData JSONLD files.

This module provides shared functionality for extracting information from
WikiData JSONLD files to avoid code duplication across different extraction scripts.
"""

import json
import os
import csv
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime


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


def parse_date(date_str):
    """Parse WikiData date string to extract year."""
    if isinstance(date_str, str) and len(date_str) >= 4:
        return int(date_str[:4])
    return None


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


def load_jsonld_file(jsonld_file_path: str) -> dict:
    """
    Load and parse a JSONLD file.
    
    Args:
        jsonld_file_path: Path to the JSONLD file
        
    Returns:
        Parsed JSON data
    """
    with open(jsonld_file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_player_id_from_filename(jsonld_file_path: str) -> Optional[str]:
    """
    Extract player ID from JSONLD filename.
    
    Args:
        jsonld_file_path: Path to the JSONLD file
        
    Returns:
        Player ID if valid filename format, None otherwise
    """
    filename = os.path.basename(jsonld_file_path)
    if filename.startswith('Q') and filename.endswith('.jsonld'):
        return filename[:-7]  # Remove .jsonld extension
    return None


def get_all_jsonld_files(directory_path: str) -> List[str]:
    """
    Get all JSONLD files in a directory.
    
    Args:
        directory_path: Path to directory containing JSONLD files
        
    Returns:
        List of full file paths
    """
    if not os.path.exists(directory_path):
        return []
    
    files = [f for f in os.listdir(directory_path) if f.endswith('.jsonld')]
    return [os.path.join(directory_path, f) for f in files]


def extract_property_value(data: dict, target_id: str, property_id: str) -> Optional[str]:
    """
    Extract a specific property value for a target entity from WikiData JSONLD.
    
    Args:
        data: The parsed JSON-LD data
        target_id: The entity ID to extract property for (e.g., 'Q107051')
        property_id: The WikiData property ID (e.g., 'P569' for date of birth)
        
    Returns:
        Property value if found, None otherwise
    """
    for item in data.get('@graph', []):
        item_id = item.get('@id', '')
        
        # Look for the target entity
        if item_id == f'wd:{target_id}' and property_id in item:
            return item.get(property_id)
    
    return None


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
