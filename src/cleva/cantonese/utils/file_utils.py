#!/usr/bin/env python3
"""
Utilities for file system operations.
"""

import json
import os
from typing import List, Optional, Dict, Any

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


def load_player_data(file_path: str) -> Dict[str, Any]:
    """Load the complete player club data."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)
