#!/usr/bin/env python3
"""
Compare Cantonese labels with language codes "yue" and "zh-hk" to check if they're identical.
"""

import sys
import os
import json
from collections import defaultdict

# Path constants
TRIPLES_DIR = "./data/soccer/intermediate/football_players_triples/"

def extract_labels_by_language(jsonld_file_path, language_codes):
    """
    Extract labels for specific language codes from a JSON-LD file.
    
    Args:
        jsonld_file_path (str): Path to the JSON-LD file
        language_codes (list): List of language codes to extract
    
    Returns:
        dict: Mapping of language codes to their label values
    """
    labels = {lang: [] for lang in language_codes}
    
    try:
        with open(jsonld_file_path, 'r', encoding='utf-8') as f:
            jsonld_data = json.load(f)
        
        if '@graph' not in jsonld_data:
            return labels
        
        for item in jsonld_data['@graph']:
            if not isinstance(item, dict):
                continue
            
            # Check specifically for the 'label' field
            if 'label' in item:
                label_data = item['label']
                if isinstance(label_data, list):
                    for label in label_data:
                        if isinstance(label, dict):
                            lang = label.get('@language')
                            if lang in language_codes:
                                value = label.get('@value', '')
                                if value:
                                    labels[lang].append(value)
                elif isinstance(label_data, dict):
                    lang = label_data.get('@language')
                    if lang in language_codes:
                        value = label_data.get('@value', '')
                        if value:
                            labels[lang].append(value)
    
    except Exception as e:
        print(f"Error processing {jsonld_file_path}: {e}")
    
    # Remove duplicates and return
    return {lang: list(set(values)) for lang, values in labels.items()}

def compare_yue_and_zh_hk():
    """Compare 'yue' and 'zh-hk' labels across all player files."""
    
    base_dir = TRIPLES_DIR
    
    if not os.path.exists(base_dir):
        print(f"Error: Directory {base_dir} does not exist.")
        return
    
    # Get all JSON-LD files
    jsonld_files = [f for f in os.listdir(base_dir) if f.endswith('.jsonld') and f.startswith('Q')]
    
    print(f"Comparing 'yue' and 'zh-hk' labels across {len(jsonld_files)} player files...")
    print("=" * 80)
    
    # Statistics
    stats = {
        'total_files': len(jsonld_files),
        'files_with_yue': 0,
        'files_with_zh_hk': 0,
        'files_with_both': 0,
        'identical_labels': 0,
        'different_labels': 0,
        'yue_only': 0,
        'zh_hk_only': 0
    }
    
    # Store differences for detailed analysis
    differences = []
    identical_cases = []
    
    for filename in sorted(jsonld_files):
        qid = filename[:-7]  # Remove .jsonld extension
        file_path = os.path.join(base_dir, filename)
        
        labels = extract_labels_by_language(file_path, ['yue', 'zh-hk'])
        
        yue_labels = labels['yue']
        zh_hk_labels = labels['zh-hk']
        
        has_yue = len(yue_labels) > 0
        has_zh_hk = len(zh_hk_labels) > 0
        
        if has_yue:
            stats['files_with_yue'] += 1
        if has_zh_hk:
            stats['files_with_zh_hk'] += 1
        if has_yue and has_zh_hk:
            stats['files_with_both'] += 1
        
        # Compare labels
        if has_yue and has_zh_hk:
            # Check if labels are identical
            yue_set = set(yue_labels)
            zh_hk_set = set(zh_hk_labels)
            
            if yue_set == zh_hk_set:
                stats['identical_labels'] += 1
                identical_cases.append({
                    'qid': qid,
                    'yue': yue_labels,
                    'zh_hk': zh_hk_labels
                })
            else:
                stats['different_labels'] += 1
                differences.append({
                    'qid': qid,
                    'yue': yue_labels,
                    'zh_hk': zh_hk_labels
                })
        elif has_yue and not has_zh_hk:
            stats['yue_only'] += 1
        elif has_zh_hk and not has_yue:
            stats['zh_hk_only'] += 1
    
    # Print results
    print("\nSTATISTICS:")
    print("-" * 40)
    print(f"Total files processed: {stats['total_files']}")
    print(f"Files with 'yue' labels: {stats['files_with_yue']}")
    print(f"Files with 'zh-hk' labels: {stats['files_with_zh_hk']}")
    print(f"Files with both languages: {stats['files_with_both']}")
    print(f"Files with identical labels: {stats['identical_labels']}")
    print(f"Files with different labels: {stats['different_labels']}")
    print(f"Files with 'yue' only: {stats['yue_only']}")
    print(f"Files with 'zh-hk' only: {stats['zh_hk_only']}")
    
    # Show differences if any
    if differences:
        print(f"\n\nDIFFERENCES FOUND ({len(differences)} cases):")
        print("-" * 50)
        for diff in differences[:10]:  # Show first 10 differences
            print(f"{diff['qid']}:")
            print(f"  yue: {diff['yue']}")
            print(f"  zh-hk: {diff['zh_hk']}")
        
        if len(differences) > 10:
            print(f"\n... and {len(differences) - 10} more differences.")
    
    # Show some identical cases for verification
    if identical_cases:
        print(f"\n\nIDENTICAL CASES (showing first 5 of {len(identical_cases)}):")
        print("-" * 50)
        for case in identical_cases[:5]:
            print(f"{case['qid']}: {case['yue'][0] if case['yue'] else 'N/A'}")
    
    # Calculate percentages
    if stats['files_with_both'] > 0:
        identical_percentage = (stats['identical_labels'] / stats['files_with_both']) * 100
        different_percentage = (stats['different_labels'] / stats['files_with_both']) * 100
        
        print(f"\n\nAMONG FILES WITH BOTH LANGUAGES:")
        print("-" * 40)
        print(f"Identical labels: {stats['identical_labels']} ({identical_percentage:.1f}%)")
        print(f"Different labels: {stats['different_labels']} ({different_percentage:.1f}%)")
    
    # Save detailed results
    results_file = "./data/soccer/intermediate/yue_vs_zh_hk_comparison.txt"
    with open(results_file, 'w', encoding='utf-8') as f:
        f.write("Comparison of 'yue' vs 'zh-hk' labels\n")
        f.write("=" * 40 + "\n\n")
        
        f.write("STATISTICS:\n")
        for key, value in stats.items():
            f.write(f"{key}: {value}\n")
        
        if differences:
            f.write(f"\n\nDIFFERENCES ({len(differences)} cases):\n")
            f.write("-" * 30 + "\n")
            for diff in differences:
                f.write(f"{diff['qid']}:\n")
                f.write(f"  yue: {diff['yue']}\n")
                f.write(f"  zh-hk: {diff['zh_hk']}\n\n")
        
        if identical_cases:
            f.write(f"\n\nIDENTICAL CASES ({len(identical_cases)} cases):\n")
            f.write("-" * 30 + "\n")
            for case in identical_cases:
                f.write(f"{case['qid']}: {case['yue']}\n")
    
    print(f"\n\nDetailed results saved to: {results_file}")

if __name__ == "__main__":
    compare_yue_and_zh_hk()
