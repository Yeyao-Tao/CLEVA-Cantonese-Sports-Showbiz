#!/usr/bin/env python3
"""
Generic Wikidata lookup module for resolving entity names to Q-IDs.

This module provides generic functionality for:
- Searching Wikidata entities by name
- Fetching entity data in JSON-LD format
- Filtering entities based on configurable criteria
- Handling Cantonese language labels

Can be used for various entity types (footballers, movies, actors, etc.)
by providing appropriate filter functions and configuration.

Requires: requests
"""
import requests
import os
import json
import time
import sys
from collections import defaultdict
from typing import Dict, List, Set, Callable, Optional, Tuple, Any

WIKIDATA_API = "https://www.wikidata.org/w/api.php"
WIKIDATA_ENTITY_DATA_URL = "https://www.wikidata.org/wiki/Special:EntityData/"

# Common Wikidata constants
Q_HUMAN = "Q5"
Q_FILM = "Q11424"
Q_ASSOC_FOOTBALL = "Q2736"
Q_ASSOC_FOOTBALL_PLAYER = "Q937857"

HEADERS = {
    # Please put a contact per Wikidata's API etiquette
    "User-Agent": "entity-qid-resolver/1.0 (your-email@example.com)"
}

def wbsearchentities(name, limit=10, language="en"):
    """Search for candidate items by label/alias."""
    params = {
        "action": "wbsearchentities",
        "search": name,
        "language": language,
        "type": "item",
        "format": "json",
        "limit": limit,
    }
    r = requests.get(WIKIDATA_API, params=params, headers=HEADERS, timeout=30)
    r.raise_for_status()
    data = r.json()
    return [hit["id"] for hit in data.get("search", [])]

def wbgetentities_claims(qids):
    """Fetch claims for many Q-IDs at once. Returns {qid: claims_dict}."""
    if not qids:
        return {}
    params = {
        "action": "wbgetentities",
        "ids": "|".join(qids),
        "props": "claims",
        "format": "json",
    }
    r = requests.get(WIKIDATA_API, params=params, headers=HEADERS, timeout=30)
    r.raise_for_status()
    entities = r.json().get("entities", {})
    return {qid: entities.get(qid, {}).get("claims", {}) for qid in qids}

def claim_object_ids(claims, pid):
    """Return a set of object Q-IDs for a given property in a claims dict."""
    out = set()
    for c in claims.get(pid, []):
        snak = c.get("mainsnak", {})
        if snak.get("snaktype") != "value":
            continue
        dv = snak.get("datavalue", {}).get("value")
        if isinstance(dv, dict) and "id" in dv:
            out.add(dv["id"])
    return out

def is_football_person(claims):
    """True if entity is a human and clearly tied to association football."""
    is_human = Q_HUMAN in claim_object_ids(claims, "P31")
    occ = claim_object_ids(claims, "P106")
    sports = claim_object_ids(claims, "P641")
    football_by_occ = Q_ASSOC_FOOTBALL_PLAYER in occ
    football_by_sport = Q_ASSOC_FOOTBALL in sports
    return is_human and (football_by_occ or football_by_sport)

def is_movie(claims):
    """True if entity is a film."""
    instance_of = claim_object_ids(claims, "P31")
    return Q_FILM in instance_of

def create_entity_filter(filter_type: str) -> Callable[[Dict], bool]:
    """
    Create an entity filter function based on the specified type.
    
    Args:
        filter_type: Type of entity filter ('football_player' or 'movie')
        
    Returns:
        Function that takes claims dict and returns True if entity matches filter
    """
    if filter_type == "football_player":
        return is_football_person
    elif filter_type == "movie":
        return is_movie
    else:
        raise ValueError(f"Unknown filter type: {filter_type}")

def resolve_entity_qids(names: List[str], 
                       entity_filter: Callable[[Dict], bool],
                       language: str = "en", 
                       search_limit: int = 10, 
                       max_candidates: int = 20) -> Tuple[Dict[str, Optional[str]], Dict[str, List[str]]]:
    """
    For each name, search candidates and keep the first one matching the filter.
    
    Args:
        names: List of entity names to search for
        entity_filter: Function to filter entities (takes claims dict, returns bool)
        language: Language for search (default: "en")
        search_limit: Maximum search results per name
        max_candidates: Maximum candidates to check per name
        
    Returns:
        result: {name: qid or None}
        debug_filtered: {name: [qid, ...]}  # candidates that were rejected
    """
    result = {}
    debug_filtered = defaultdict(list)
    
    total_names = len(names)
    start_time = time.time()

    for idx, name in enumerate(names, 1):
        print(f"Processing {idx}/{total_names}: {name}")
        
        # 1) search candidates
        search_start = time.time()
        qids = wbsearchentities(name, limit=search_limit, language=language)
        search_time = time.time() - search_start
        print(f"  Found {len(qids)} candidates in {search_time:.2f}s")

        # 2) check them in small batches to respect URL size limits
        picked = None
        batch_start = time.time()
        for i in range(0, min(len(qids), max_candidates), 50):
            batch = qids[i:i+50]
            print(f"  Checking batch {i//50 + 1} ({len(batch)} candidates)...")
            claims_map = wbgetentities_claims(batch)
            for qid in batch:
                claims = claims_map.get(qid, {})
                if entity_filter(claims):
                    picked = qid
                    print(f"  ✓ Found matching entity: {qid}")
                    break
                else:
                    debug_filtered[name].append(qid)
            if picked:
                break
        
        batch_time = time.time() - batch_start
        if not picked:
            print(f"  ✗ No matching entity found (checked in {batch_time:.2f}s)")
        
        result[name] = picked
        
        # Progress estimation
        elapsed = time.time() - start_time
        avg_time_per_name = elapsed / idx
        remaining_names = total_names - idx
        eta_seconds = remaining_names * avg_time_per_name
        eta_minutes = eta_seconds / 60
        
        print(f"  Progress: {idx}/{total_names} ({idx/total_names*100:.1f}%) - ETA: {eta_minutes:.1f} minutes\n")

    total_time = time.time() - start_time
    print(f"Completed entity resolution in {total_time/60:.1f} minutes")
    return result, debug_filtered

def read_names_from_file(file_path):
    """Read player names from a text file, one name per line."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Names file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        names = [line.strip() for line in f if line.strip()]
    
    return names

def has_cantonese_label(jsonld_data):
    """
    Check if the JSON-LD data contains Cantonese labels in the 'label' field.
    First checks for 'yue', then falls back to 'zh-hk' if no 'yue' label found.
    
    Args:
        jsonld_data (dict): The parsed JSON-LD data
    
    Returns:
        bool: True if entity has Cantonese labels, False otherwise
    """
    if not isinstance(jsonld_data, dict) or '@graph' not in jsonld_data:
        return False
    
    has_yue = False
    has_zh_hk = False
    
    for item in jsonld_data['@graph']:
        if not isinstance(item, dict):
            continue
            
        # Check specifically for the 'label' field with Cantonese languages
        if 'label' in item:
            labels = item['label']
            if isinstance(labels, list):
                for label in labels:
                    if isinstance(label, dict):
                        lang = label.get('@language')
                        if lang == 'yue':
                            has_yue = True
                        elif lang == 'zh-hk':
                            has_zh_hk = True
            elif isinstance(labels, dict):
                lang = labels.get('@language')
                if lang == 'yue':
                    has_yue = True
                elif lang == 'zh-hk':
                    has_zh_hk = True
    
    # Return True if we have 'yue' labels, or if we have 'zh-hk' labels as fallback
    return has_yue or has_zh_hk

def fetch_entity_jsonld(qid: str, output_dir: str, filter_cantonese: bool = False) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Fetch JSON-LD triples for a Wikidata entity (Q-ID) and optionally save to file.
    
    Args:
        qid (str): The Wikidata Q-ID (e.g., "Q41421")
        output_dir (str): Directory to save the JSON-LD file
        filter_cantonese (bool): If True, only save if entity has Cantonese labels
    
    Returns:
        tuple: (jsonld_data, file_path) where:
            - jsonld_data: The parsed JSON-LD data (dict) or None if failed
            - file_path: Path to saved file or None if not saved/failed
    """
    if not qid:
        return None, None
        
    try:
        # Construct the URL for JSON-LD data
        url = f"{WIKIDATA_ENTITY_DATA_URL}{qid}.jsonld"
        
        # Make the request
        print(f"    Fetching from: {url}")
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        # Parse JSON to validate it
        jsonld_data = response.json()
        
        # If filtering is enabled, check for Cantonese labels before saving
        if filter_cantonese:
            if not has_cantonese_label(jsonld_data):
                print(f"    ✗ {qid} does not have Cantonese labels - not saving")
                return jsonld_data, None
            else:
                print(f"    ✓ {qid} has Cantonese labels - proceeding to save")
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Save to file
        output_file = os.path.join(output_dir, f"{qid}.jsonld")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(jsonld_data, f, indent=2, ensure_ascii=False)
        
        print(f"    ✓ Saved JSON-LD for {qid} to {output_file}")
        return jsonld_data, output_file
        
    except requests.RequestException as e:
        print(f"    ✗ Error fetching JSON-LD for {qid}: {e}")
        return None, None
    except json.JSONDecodeError as e:
        print(f"    ✗ Error parsing JSON-LD for {qid}: {e}")
        return None, None
    except Exception as e:
        print(f"    ✗ Unexpected error for {qid}: {e}")
        return None, None

def fetch_all_entity_triples(qid_mapping: Dict[str, Optional[str]], 
                           output_dir: str, 
                           filter_cantonese: bool = False,
                           entity_type: str = "entity") -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
    """
    Fetch JSON-LD triples for all resolved entities.
    
    Args:
        qid_mapping: Mapping of entity names to Q-IDs
        output_dir: Directory to save the JSON-LD files
        filter_cantonese: If True, only save files for entities with Cantonese labels
        entity_type: Type of entity for logging purposes (e.g., "player", "movie")
    
    Returns:
        dict: Mapping of Q-IDs to saved file paths (only for entities with Cantonese labels if filtering)
        dict: Mapping of Q-IDs to entity names for entities with Cantonese labels
        dict: Mapping of Q-IDs to entity names for entities without Cantonese labels (if filtering)
    """
    saved_files = {}
    entities_with_cantonese = {}
    entities_without_cantonese = {}
    successful_fetches = 0
    
    # Count how many entities have Q-IDs
    entities_with_qids = [(name, qid) for name, qid in qid_mapping.items() if qid]
    total_to_fetch = len(entities_with_qids)
    
    if filter_cantonese:
        print(f"\nFetching JSON-LD triples for {total_to_fetch} {entity_type}s and filtering for Cantonese labels...")
    else:
        print(f"\nFetching JSON-LD triples for {total_to_fetch} {entity_type}s with Q-IDs...")
    
    start_time = time.time()
    for idx, (name, qid) in enumerate(entities_with_qids, 1):
        print(f"Processing {idx}/{total_to_fetch}: {name} ({qid})")
        jsonld_data, file_path = fetch_entity_jsonld(qid, output_dir, filter_cantonese)
        
        if jsonld_data is not None:  # Successfully fetched data
            successful_fetches += 1
            if filter_cantonese:
                if file_path is not None:  # Has Cantonese labels and was saved
                    saved_files[qid] = file_path
                    entities_with_cantonese[qid] = name
                    print(f"    ✓ {name} ({qid}) has Cantonese labels - saved")
                else:  # No Cantonese labels, not saved
                    entities_without_cantonese[qid] = name
                    print(f"    ✗ {name} ({qid}) does not have Cantonese labels - not saved")
            else:
                if file_path is not None:  # Successfully saved (no filtering)
                    saved_files[qid] = file_path
        
        # Progress estimation for triple fetching
        if idx % 5 == 0 or idx == total_to_fetch:  # Show progress every 5 items or at the end
            elapsed = time.time() - start_time
            avg_time_per_fetch = elapsed / idx
            remaining = total_to_fetch - idx
            eta_seconds = remaining * avg_time_per_fetch
            eta_minutes = eta_seconds / 60
            print(f"  Progress: {idx}/{total_to_fetch} ({idx/total_to_fetch*100:.1f}%) - ETA: {eta_minutes:.1f} minutes\n")
    
    # Skip entities without Q-IDs
    skipped_count = len(qid_mapping) - total_to_fetch
    if skipped_count > 0:
        print(f"Skipped {skipped_count} {entity_type}s without Q-IDs")
    
    total_time = time.time() - start_time
    print(f"\nCompleted processing in {total_time/60:.1f} minutes")
    print(f"Successfully fetched data for {successful_fetches}/{total_to_fetch} {entity_type}s with Q-IDs")
    
    if filter_cantonese:
        print(f"Saved JSON-LD files for {len(saved_files)} {entity_type}s with Cantonese labels")
        print(f"Filtered out {len(entities_without_cantonese)} {entity_type}s without Cantonese labels")
        return saved_files, entities_with_cantonese, entities_without_cantonese
    else:
        print(f"Saved JSON-LD files for {len(saved_files)} {entity_type}s")
        return saved_files, {}, {}

def filter_entities_with_cantonese_labels(saved_files: Dict[str, str], entity_type: str = "entity") -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Filter entities to keep only those with Cantonese labels.
    
    Args:
        saved_files: Mapping of Q-IDs to saved file paths
        entity_type: Type of entity for logging purposes (e.g., "player", "movie")
    
    Returns:
        dict: Mapping of Q-IDs to file paths for entities with Cantonese labels
        dict: Mapping of Q-IDs to file paths for entities without Cantonese labels
    """
    entities_with_cantonese = {}
    entities_without_cantonese = {}
    
    print(f"\nFiltering {entity_type}s based on Cantonese labels...")
    
    for qid, file_path in saved_files.items():
        print(f"Checking {qid} for Cantonese labels...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                jsonld_data = json.load(f)
            
            if has_cantonese_label(jsonld_data):
                entities_with_cantonese[qid] = file_path
                print(f"  ✓ {qid} has Cantonese labels")
            else:
                entities_without_cantonese[qid] = file_path
                print(f"  ✗ {qid} does not have Cantonese labels")
                
        except Exception as e:
            print(f"  ✗ Error reading {file_path}: {e}")
            entities_without_cantonese[qid] = file_path
    
    print(f"\nCantonese label filtering complete:")
    print(f"- {entity_type.title()}s with Cantonese labels: {len(entities_with_cantonese)}")
    print(f"- {entity_type.title()}s without Cantonese labels: {len(entities_without_cantonese)}")
    
    return entities_with_cantonese, entities_without_cantonese

def filter_existing_entities_for_cantonese(input_dir: str, entity_type: str = "entity") -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Filter existing JSON-LD files to find entities with Cantonese labels.
    
    Args:
        input_dir: Directory containing the JSON-LD files
        entity_type: Type of entity for logging purposes (e.g., "player", "movie")
    
    Returns:
        dict: Mapping of Q-IDs to file paths for entities with Cantonese labels
        dict: Mapping of Q-IDs to file paths for entities without Cantonese labels
    """
    if not os.path.exists(input_dir):
        print(f"Error: Directory {input_dir} does not exist.")
        return {}, {}
    
    # Get all JSON-LD files in the directory
    saved_files = {}
    for filename in os.listdir(input_dir):
        if filename.endswith('.jsonld') and filename.startswith('Q'):
            qid = filename[:-7]  # Remove .jsonld extension
            saved_files[qid] = os.path.join(input_dir, filename)
    
    print(f"Found {len(saved_files)} JSON-LD files in {input_dir}")
    
    if not saved_files:
        print("No JSON-LD files found to process.")
        return {}, {}
    
    return filter_entities_with_cantonese_labels(saved_files, entity_type)

# This module provides generic functions for Wikidata entity lookup
# See specific implementation scripts in soccer/ and entertainment/ directories
