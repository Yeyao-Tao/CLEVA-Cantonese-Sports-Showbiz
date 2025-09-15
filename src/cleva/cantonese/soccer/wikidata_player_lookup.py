#!/usr/bin/env python3
"""
Soccer player specific Wikidata lookup script.

This script uses the generic wikidata_lookup module to resolve
soccer player names to Wikidata Q-IDs and fetch their JSON-LD data.

Filters for football players specifically by requiring:
  - P31 (instance of) includes Q5 (human), AND
  - (P106 (occupation) includes Q937857 association football player) OR
    (P641 (sport) includes Q2736 association football)

The script filters for Cantonese labels during the data fetching process,
only saving JSON-LD files for players who have Cantonese (yue) or Hong Kong Chinese (zh-hk) labels.

Requires: requests
"""
import os
import sys

# Add the parent directory to the path to import the generic wikidata_lookup module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wikidata_lookup import (
    resolve_entity_qids, 
    fetch_all_entity_triples,
    create_entity_filter,
    read_names_from_file
)
from utils.path_utils import get_football_players_triples_dir, get_soccer_intermediate_dir

# Path constants
TRIPLES_DIR = get_football_players_triples_dir() + "/"

def main():
    """Main function to resolve soccer player Q-IDs and fetch their data."""
    # Read player names from the file created by fifa_dataset_lookup.py
    names_file = os.path.join(get_soccer_intermediate_dir(), "fifa_player_names.txt")
    
    try:
        names = read_names_from_file(names_file)
        print(f"Loaded {len(names)} player names from {names_file}")
        print("Starting player Q-ID resolution...\n")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please run fifa_dataset_lookup.py first to generate the names file.")
        exit(1)
    
    # Create football player filter
    football_filter = create_entity_filter("football_player")
    
    # names = names[:10]  # Uncomment for testing with smaller subset
    # Resolve Q-IDs for all players
    mapping, filtered = resolve_entity_qids(names, football_filter)

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

    # Fetch JSON-LD triples for all resolved players and filter for Cantonese labels
    saved_files, players_with_cantonese, players_without_cantonese = fetch_all_entity_triples(
        mapping, 
        TRIPLES_DIR, 
        filter_cantonese=True,
        entity_type="player"
    )
    
    print(f"\n" + "="*50)
    print("FINAL SUMMARY:")
    print("="*50)
    print(f"- Total players processed: {len(names)}")
    print(f"- Players with Q-IDs found: {resolved_count}")
    print(f"- Players with Cantonese labels: {len(players_with_cantonese)}")
    print(f"- Players without Cantonese labels: {len(players_without_cantonese)}")
    print(f"- JSON-LD files saved: {len(saved_files)} (only for players with Cantonese labels)")
    print(f"- Files saved to: {TRIPLES_DIR}")
    
    if players_with_cantonese:
        print(f"\nPlayers with Cantonese labels:")
        for qid, name in players_with_cantonese.items():
            print(f"  - {name} ({qid})")
    
    # Save the list of players with Cantonese labels to a file
    cantonese_players_file = os.path.join(get_soccer_intermediate_dir(), "players_with_cantonese_labels.txt")
    with open(cantonese_players_file, 'w', encoding='utf-8') as f:
        for qid in players_with_cantonese:
            f.write(f"{qid}\n")
    print(f"\nList of players with Cantonese labels saved to: {cantonese_players_file}")

if __name__ == "__main__":
    main()
