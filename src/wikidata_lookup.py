#!/usr/bin/env python3
"""
Resolve player names -> Wikidata Q-IDs (footballers only).

Filters out non-people (books, trials, photos) and non-footballers by requiring:
  - P31 (instance of) includes Q5 (human), AND
  - (P106 (occupation) includes Q937857 association football player) OR
    (P641 (sport) includes Q2736 association football)

Requires: requests
"""
import requests
import os
import json
import time
from collections import defaultdict

WIKIDATA_API = "https://www.wikidata.org/w/api.php"
WIKIDATA_ENTITY_DATA_URL = "https://www.wikidata.org/wiki/Special:EntityData/"

# Path constants
TRIPLES_DIR = "./data/intermediate/football_players_triples/"

# Wikidata constants
Q_HUMAN = "Q5"
Q_ASSOC_FOOTBALL = "Q2736"
Q_ASSOC_FOOTBALL_PLAYER = "Q937857"

HEADERS = {
    # Please put a contact per Wikidata's API etiquette
    "User-Agent": "player-qid-resolver/1.0 (your-email@example.com)"
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

def resolve_player_qids(names, language="en", search_limit=10, max_candidates=20):
    """
    For each name, search candidates and keep the first 'football person'.
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
                if is_football_person(claims):
                    picked = qid
                    print(f"  ✓ Found football player: {qid}")
                    break
                else:
                    debug_filtered[name].append(qid)
            if picked:
                break
        
        batch_time = time.time() - batch_start
        if not picked:
            print(f"  ✗ No football player found (checked in {batch_time:.2f}s)")
        
        result[name] = picked
        
        # Progress estimation
        elapsed = time.time() - start_time
        avg_time_per_name = elapsed / idx
        remaining_names = total_names - idx
        eta_seconds = remaining_names * avg_time_per_name
        eta_minutes = eta_seconds / 60
        
        print(f"  Progress: {idx}/{total_names} ({idx/total_names*100:.1f}%) - ETA: {eta_minutes:.1f} minutes\n")

    total_time = time.time() - start_time
    print(f"Completed player resolution in {total_time/60:.1f} minutes")
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

def fetch_entity_jsonld(qid, output_dir=TRIPLES_DIR):
    """
    Fetch JSON-LD triples for a Wikidata entity (Q-ID) and save to file.
    
    Args:
        qid (str): The Wikidata Q-ID (e.g., "Q41421")
        output_dir (str): Directory to save the JSON-LD file
    
    Returns:
        str: Path to the saved file, or None if failed
    """
    if not qid:
        return None
        
    try:
        # Construct the URL for JSON-LD data
        url = f"{WIKIDATA_ENTITY_DATA_URL}{qid}.jsonld"
        
        # Make the request
        print(f"    Fetching from: {url}")
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        # Parse JSON to validate it
        jsonld_data = response.json()
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Save to file
        output_file = os.path.join(output_dir, f"{qid}.jsonld")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(jsonld_data, f, indent=2, ensure_ascii=False)
        
        print(f"    ✓ Saved JSON-LD for {qid} to {output_file}")
        return output_file
        
    except requests.RequestException as e:
        print(f"    ✗ Error fetching JSON-LD for {qid}: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"    ✗ Error parsing JSON-LD for {qid}: {e}")
        return None
    except Exception as e:
        print(f"    ✗ Unexpected error for {qid}: {e}")
        return None

def fetch_all_player_triples(qid_mapping, output_dir=TRIPLES_DIR):
    """
    Fetch JSON-LD triples for all resolved players.
    
    Args:
        qid_mapping (dict): Mapping of player names to Q-IDs
        output_dir (str): Directory to save the JSON-LD files
    
    Returns:
        dict: Mapping of Q-IDs to saved file paths
    """
    saved_files = {}
    successful_fetches = 0
    
    # Count how many players have Q-IDs
    players_with_qids = [(name, qid) for name, qid in qid_mapping.items() if qid]
    total_to_fetch = len(players_with_qids)
    
    print(f"\nFetching JSON-LD triples for {total_to_fetch} players with Q-IDs...")
    
    start_time = time.time()
    for idx, (name, qid) in enumerate(players_with_qids, 1):
        print(f"Fetching {idx}/{total_to_fetch}: {name} ({qid})")
        file_path = fetch_entity_jsonld(qid, output_dir)
        if file_path:
            saved_files[qid] = file_path
            successful_fetches += 1
        
        # Progress estimation for triple fetching
        if idx % 5 == 0 or idx == total_to_fetch:  # Show progress every 5 items or at the end
            elapsed = time.time() - start_time
            avg_time_per_fetch = elapsed / idx
            remaining = total_to_fetch - idx
            eta_seconds = remaining * avg_time_per_fetch
            eta_minutes = eta_seconds / 60
            print(f"  Triple fetching progress: {idx}/{total_to_fetch} ({idx/total_to_fetch*100:.1f}%) - ETA: {eta_minutes:.1f} minutes\n")
    
    # Skip players without Q-IDs
    skipped_count = len(qid_mapping) - total_to_fetch
    if skipped_count > 0:
        print(f"Skipped {skipped_count} players without Q-IDs")
    
    total_time = time.time() - start_time
    print(f"\nCompleted triple fetching in {total_time/60:.1f} minutes")
    print(f"Successfully fetched triples for {successful_fetches}/{total_to_fetch} players with Q-IDs")
    return saved_files

def filter_players_with_cantonese_labels(saved_files):
    """
    Filter players to keep only those with Cantonese labels.
    
    Args:
        saved_files (dict): Mapping of Q-IDs to saved file paths
    
    Returns:
        dict: Mapping of Q-IDs to file paths for players with Cantonese labels
        dict: Mapping of Q-IDs to file paths for players without Cantonese labels
    """
    players_with_cantonese = {}
    players_without_cantonese = {}
    
    print(f"\nFiltering players based on Cantonese labels...")
    
    for qid, file_path in saved_files.items():
        print(f"Checking {qid} for Cantonese labels...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                jsonld_data = json.load(f)
            
            if has_cantonese_label(jsonld_data):
                players_with_cantonese[qid] = file_path
                print(f"  ✓ {qid} has Cantonese labels")
            else:
                players_without_cantonese[qid] = file_path
                print(f"  ✗ {qid} does not have Cantonese labels")
                
        except Exception as e:
            print(f"  ✗ Error reading {file_path}: {e}")
            players_without_cantonese[qid] = file_path
    
    print(f"\nCantonese label filtering complete:")
    print(f"- Players with Cantonese labels: {len(players_with_cantonese)}")
    print(f"- Players without Cantonese labels: {len(players_without_cantonese)}")
    
    return players_with_cantonese, players_without_cantonese

def filter_existing_players_for_cantonese(input_dir=TRIPLES_DIR):
    """
    Filter existing JSON-LD files to find players with Cantonese labels.
    
    Args:
        input_dir (str): Directory containing the JSON-LD files
    
    Returns:
        dict: Mapping of Q-IDs to file paths for players with Cantonese labels
        dict: Mapping of Q-IDs to file paths for players without Cantonese labels
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
    
    return filter_players_with_cantonese_labels(saved_files)

if __name__ == "__main__":
    # Read player names from the file created by fifa_dataset_lookup.py
    names_file = "./data/intermediate/fifa_player_names.txt"
    
    try:
        names = read_names_from_file(names_file)
        print(f"Loaded {len(names)} player names from {names_file}")
        print("Starting player Q-ID resolution...\n")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please run fifa_dataset_lookup.py first to generate the names file.")
        exit(1)
    
    # names = names[:10]
    # Resolve Q-IDs for all players
    mapping, filtered = resolve_player_qids(names)

    print("\n" + "="*50)
    print("RESOLUTION COMPLETE - RESULTS:")
    print("="*50)
    
    resolved_count = len([qid for qid in mapping.values() if qid])
    print(f"Players with Q-IDs found: {resolved_count}/{len(names)}")
    
    print("\nResolved mapping:")
    for nm, qid in mapping.items():
        status = "✓" if qid else "✗"
        print(f"  {status} {nm} -> {qid}")

    print("\nFiltered-out candidates (not football *people*):")
    for nm, qids in filtered.items():
        if qids:
            print(f"  {nm}: {', '.join(qids)}")

    # Fetch JSON-LD triples for all resolved players
    saved_files = fetch_all_player_triples(mapping)
    
    # Filter players based on Cantonese labels
    players_with_cantonese, players_without_cantonese = filter_players_with_cantonese_labels(saved_files)
    
    print(f"\n" + "="*50)
    print("FINAL SUMMARY:")
    print("="*50)
    print(f"- Total players processed: {len(names)}")
    print(f"- Players with Q-IDs found: {resolved_count}")
    print(f"- JSON-LD files saved: {len(saved_files)}")
    print(f"- Players with Cantonese labels: {len(players_with_cantonese)}")
    print(f"- Players without Cantonese labels: {len(players_without_cantonese)}")
    print(f"- Files saved to: {TRIPLES_DIR}")
    
    if players_with_cantonese:
        print(f"\nPlayers with Cantonese labels:")
        for qid in players_with_cantonese:
            print(f"  - {qid}")
    
    # Save the list of players with Cantonese labels to a file
    cantonese_players_file = "./data/intermediate/players_with_cantonese_labels.txt"
    with open(cantonese_players_file, 'w', encoding='utf-8') as f:
        for qid in players_with_cantonese:
            f.write(f"{qid}\n")
    print(f"\nList of players with Cantonese labels saved to: {cantonese_players_file}")
