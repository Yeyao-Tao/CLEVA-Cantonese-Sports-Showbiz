#!/usr/bin/env python3
"""
Common utilities for reading and parsing WikiData JSONLD files.

This module provides shared functionality for extracting information from
WikiData JSONLD files to avoid code duplication across different extraction scripts.
"""

import json
from typing import Dict, Any, Optional

from .cantonese_utils import get_best_cantonese_name


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
