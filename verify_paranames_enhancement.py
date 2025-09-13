#!/usr/bin/env python3
"""
Verify ParaNames enhancement statistics in the output data.
"""

import json

def main():
    with open('data/soccer/intermediate/football_players_clubs_complete.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Count sources
    player_wikidata = 0
    player_paranames = 0
    club_wikidata = 0
    club_paranames = 0
    club_none = 0
    
    paranames_enhanced_clubs = set()
    
    for player_id, player_data in data['players'].items():
        # Check player source
        player_source = player_data['player_names'].get('cantonese_source', 'none')
        if player_source == 'wikidata':
            player_wikidata += 1
        elif player_source == 'paranames':
            player_paranames += 1
        
        # Check club sources
        for club in player_data['clubs']:
            if club['has_cantonese']:
                club_source = club['club_names'].get('cantonese_source', 'none')
                if club_source == 'wikidata':
                    club_wikidata += 1
                elif club_source == 'paranames':
                    club_paranames += 1
                    paranames_enhanced_clubs.add(club['club_id'])
                else:
                    club_none += 1
    
    print("ParaNames Enhancement Verification:")
    print("=" * 50)
    print(f"Total players: {len(data['players'])}")
    print(f"Player names from WikiData: {player_wikidata}")
    print(f"Player names from ParaNames: {player_paranames}")
    print()
    print(f"Club entries with Cantonese: {club_wikidata + club_paranames + club_none}")
    print(f"Club names from WikiData: {club_wikidata}")
    print(f"Club names from ParaNames: {club_paranames}")
    print(f"Club names with no source: {club_none}")
    print(f"Unique clubs enhanced by ParaNames: {len(paranames_enhanced_clubs)}")
    
    # Show some examples
    print("\nSample clubs enhanced by ParaNames:")
    count = 0
    for player_id, player_data in data['players'].items():
        for club in player_data['clubs']:
            if (club['has_cantonese'] and 
                club['club_names'].get('cantonese_source') == 'paranames'):
                print(f"  {club['club_id']} ({club['name']}): {club['cantonese_name']}")
                count += 1
                if count >= 10:
                    break
        if count >= 10:
            break

if __name__ == "__main__":
    main()
