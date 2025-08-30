#!/usr/bin/env python3
"""
Test script to filter existing players and find those with Cantonese labels.
"""

import sys
import os

# Add src directory to path so we can import our module
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from wikidata_lookup import filter_existing_players_for_cantonese

if __name__ == "__main__":
    print("Testing Cantonese label filtering on existing player data...")
    
    # Filter existing players
    players_with_cantonese, players_without_cantonese = filter_existing_players_for_cantonese()
    
    print(f"\n" + "="*60)
    print("CANTONESE FILTERING TEST RESULTS:")
    print("="*60)
    print(f"- Players with Cantonese labels: {len(players_with_cantonese)}")
    print(f"- Players without Cantonese labels: {len(players_without_cantonese)}")
    
    if players_with_cantonese:
        print(f"\nPlayers with Cantonese labels:")
        for qid in sorted(players_with_cantonese.keys()):
            print(f"  - {qid}")
    
    # Save the results
    output_file = "./data/intermediate/cantonese_players_test.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("Players with Cantonese labels:\n")
        for qid in sorted(players_with_cantonese.keys()):
            f.write(f"{qid}\n")
    
    print(f"\nResults saved to: {output_file}")
