#!/usr/bin/env python3
"""
Simple Lua Movie Parser - Quick Example

A minimal example showing how to extract movie names from the Lua file.
"""

import re
import json


def parse_lua_movies(file_path):
    """
    Simple function to parse movie names from Lua file.
    
    Returns:
        Dictionary mapping English names to their Chinese translations
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all Item() calls with movie data
    pattern = r"Item\('([^']+)',\s*'([^']+)'"
    matches = re.findall(pattern, content)
    
    movies = {}
    
    for english_name, translation_rules in matches:
        if not english_name:  # Skip empty names
            continue
            
        # Parse the translation rules
        translations = {}
        
        # Split by semicolon and extract language-translation pairs
        for rule in translation_rules.split(';'):
            if ':' in rule:
                # Handle both "zh-code:translation" and "original=>zh-code:translation"
                if '=>' in rule:
                    rule = rule.split('=>')[-1]  # Take the part after '=>'
                
                if ':' in rule:
                    lang_code, translation = rule.split(':', 1)
                    translations[lang_code.strip()] = translation.strip()
        
        movies[english_name] = translations
    
    return movies


def get_cantonese_movies(movies_dict):
    """Extract movies with Cantonese (Hong Kong) translations."""
    cantonese_movies = {}
    
    for english_name, translations in movies_dict.items():
        # Look for Hong Kong Cantonese (zh-hk) first, then Macau (zh-mo)
        for lang_code in ['zh-hk', 'zh-mo']:
            if lang_code in translations:
                cantonese_movies[english_name] = translations[lang_code]
                break
    
    return cantonese_movies


# Example usage
if __name__ == "__main__":
    # Parse the Lua file
    lua_file_path = '/Users/taoyeyao/workplace/CLEVA-Cantonese-Sports-Showbiz/data/entertainment/raw/cgroup_movie.lua'
    
    print("Parsing Lua movie file...")
    movies = parse_lua_movies(lua_file_path)
    
    print(f"Found {len(movies)} movies total")
    
    # Get Cantonese translations
    cantonese_movies = get_cantonese_movies(movies)
    print(f"Found {len(cantonese_movies)} movies with Cantonese translations")
    
    # Show some examples
    print("\n=== Sample English → Cantonese translations ===")
    count = 0
    for english, cantonese in cantonese_movies.items():
        print(f"{english} → {cantonese}")
        count += 1
        if count >= 10:  # Show first 10
            break
    
    # Show all Chinese variants for a specific movie
    print(f"\n=== All translations for 'Titanic' ===")
    if 'Titanic' in movies:
        for lang_code, translation in movies['Titanic'].items():
            print(f"{lang_code}: {translation}")
    
    # Save to JSON files
    print(f"\nSaving data...")
    
    # Save all movies with all translations
    with open('movies_simple_all.json', 'w', encoding='utf-8') as f:
        json.dump(movies, f, ensure_ascii=False, indent=2)
    
    # Save just English-Cantonese pairs
    with open('movies_simple_cantonese.json', 'w', encoding='utf-8') as f:
        json.dump(cantonese_movies, f, ensure_ascii=False, indent=2)
    
    print("Files saved:")
    print("- movies_simple_all.json")
    print("- movies_simple_cantonese.json")
