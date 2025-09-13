#!/usr/bin/env python3
"""
Enhanced test script to find Cantonese labels and show examples.
"""

import sys
import os
import json

# Add src directory to path so we can import our module
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from wikidata_lookup import filter_existing_players_for_cantonese, TRIPLES_DIR

def extract_cantonese_names(jsonld_file_path):
    """
    Extract Cantonese labels from the 'label' field in a JSON-LD file.
    Prioritizes 'yue' labels, falls back to 'zh-hk' if no 'yue' labels found.
    """
    yue_labels = []
    zh_hk_labels = []
    
    try:
        with open(jsonld_file_path, 'r', encoding='utf-8') as f:
            jsonld_data = json.load(f)
        
        if '@graph' not in jsonld_data:
            return []
        
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
                            value = label.get('@value', '')
                            if value:
                                if lang == 'yue':
                                    yue_labels.append(value)
                                elif lang == 'zh-hk':
                                    zh_hk_labels.append(value)
                elif isinstance(labels, dict):
                    lang = labels.get('@language')
                    value = labels.get('@value', '')
                    if value:
                        if lang == 'yue':
                            yue_labels.append(value)
                        elif lang == 'zh-hk':
                            zh_hk_labels.append(value)
    
    except Exception as e:
        print(f"Error extracting labels from {jsonld_file_path}: {e}")
    
    # Prioritize 'yue' labels, fall back to 'zh-hk' if no 'yue' found
    if yue_labels:
        return list(set(yue_labels))  # Remove duplicates
    else:
        return list(set(zh_hk_labels))  # Remove duplicates

if __name__ == "__main__":
    print("Enhanced Cantonese label analysis...")
    print(f"Using triples directory: {TRIPLES_DIR}")
    
    # Filter existing players
    players_with_cantonese, players_without_cantonese = filter_existing_players_for_cantonese()
    
    print(f"\n" + "="*60)
    print("DETAILED CANTONESE ANALYSIS:")
    print("="*60)
    
    # Show examples of Cantonese names
    examples_count = 0
    for qid, file_path in list(players_with_cantonese.items()):  # Show first 10 examples
        cantonese_labels = extract_cantonese_names(file_path)
        if cantonese_labels:
            examples_count += 1
            print(f"{qid}: {', '.join(cantonese_labels[:3])}{'...' if len(cantonese_labels) > 3 else ''}")
    
    print(f"\nShowing {examples_count} examples (total: {len(players_with_cantonese)} players with Cantonese labels)")
    print(f"Players without Cantonese labels: {len(players_without_cantonese)}")
    
    # Save detailed results
    detailed_output = "./data/soccer/intermediate/cantonese_players_detailed.txt"
    with open(detailed_output, 'w', encoding='utf-8') as f:
        f.write("Players with Cantonese labels and their names:\n")
        f.write("="*50 + "\n\n")
        
        for qid in sorted(players_with_cantonese.keys()):
            file_path = players_with_cantonese[qid]
            cantonese_labels = extract_cantonese_names(file_path)
            f.write(f"{qid}: {', '.join(cantonese_labels)}\n")
        
        f.write(f"\n\nSummary:\n")
        f.write(f"- Total players with Cantonese labels: {len(players_with_cantonese)}\n")
        f.write(f"- Total players without Cantonese labels: {len(players_without_cantonese)}\n")
    
    print(f"\nDetailed results saved to: {detailed_output}")
