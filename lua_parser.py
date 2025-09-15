#!/usr/bin/env python3
"""
Lua Movie Data Parser

This script parses the cgroup_movie.lua file to extract movie names
in English and various Chinese variants (Cantonese, Traditional Chinese, 
Simplified Chinese, etc.).
"""

import re
import json
from typing import Dict, List, Optional, Tuple


class LuaMovieParser:
    """Parser for the Lua movie translation file."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.movies = []
        
    def parse_file(self) -> List[Dict]:
        """
        Parse the Lua file and extract movie data.
        
        Returns:
            List of dictionaries containing movie names and translations
        """
        with open(self.file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all Item() function calls
        item_pattern = r"Item\('([^']*)',\s*'([^']*)'"
        matches = re.findall(item_pattern, content)
        
        for match in matches:
            english_name, translation_rules = match
            
            # Skip items without English names (these are just conversion rules)
            if not english_name:
                continue
                
            # Parse translation rules
            translations = self._parse_translation_rules(translation_rules)
            
            movie_data = {
                'english_name': english_name,
                'translations': translations
            }
            
            self.movies.append(movie_data)
        
        return self.movies
    
    def _parse_translation_rules(self, rules: str) -> Dict[str, str]:
        """
        Parse the translation rules string.
        
        Args:
            rules: String containing translation rules like 'zh-tw:中文;zh-cn:中文;'
            
        Returns:
            Dictionary mapping language codes to translations
        """
        translations = {}
        
        # Split by semicolon and process each rule
        rule_parts = rules.split(';')
        
        for part in rule_parts:
            part = part.strip()
            if not part:
                continue
                
            # Handle different formats
            if '=>' in part:
                # Format: "original=>zh-code:translation"
                if '=>' in part:
                    _, translation_part = part.split('=>', 1)
                    if ':' in translation_part:
                        lang_code, translation = translation_part.split(':', 1)
                        translations[lang_code] = translation
            elif ':' in part:
                # Format: "zh-code:translation"
                lang_code, translation = part.split(':', 1)
                translations[lang_code] = translation
        
        return translations
    
    def get_cantonese_names(self) -> List[Tuple[str, str]]:
        """
        Extract movies with Cantonese (Hong Kong) translations.
        
        Returns:
            List of tuples (english_name, cantonese_name)
        """
        cantonese_movies = []
        
        for movie in self.movies:
            translations = movie['translations']
            
            # Look for Hong Kong Cantonese translations
            for lang_code in ['zh-hk', 'zh-mo']:  # Hong Kong and Macau
                if lang_code in translations:
                    cantonese_movies.append((
                        movie['english_name'], 
                        translations[lang_code]
                    ))
                    break  # Take the first available Cantonese translation
        
        return cantonese_movies
    
    def get_all_chinese_variants(self, english_name: str) -> Dict[str, str]:
        """
        Get all Chinese variants for a specific English movie name.
        
        Args:
            english_name: The English name of the movie
            
        Returns:
            Dictionary of language codes to translations
        """
        for movie in self.movies:
            if movie['english_name'] == english_name:
                return movie['translations']
        
        return {}
    
    def save_to_json(self, output_path: str):
        """Save parsed data to JSON file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.movies, f, ensure_ascii=False, indent=2)
    
    def save_cantonese_mapping(self, output_path: str):
        """Save English-Cantonese mapping to JSON file."""
        cantonese_data = {}
        
        for movie in self.movies:
            translations = movie['translations']
            english_name = movie['english_name']
            
            # Get Cantonese translation (prioritize zh-hk)
            cantonese_name = None
            for lang_code in ['zh-hk', 'zh-mo']:
                if lang_code in translations:
                    cantonese_name = translations[lang_code]
                    break
            
            if cantonese_name:
                cantonese_data[english_name] = cantonese_name
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(cantonese_data, f, ensure_ascii=False, indent=2)


def main():
    """Example usage of the parser."""
    
    # Initialize parser
    parser = LuaMovieParser('/Users/taoyeyao/workplace/CLEVA-Cantonese-Sports-Showbiz/data/entertainment/raw/cgroup_movie.lua')
    
    # Parse the file
    movies = parser.parse_file()
    
    print(f"Parsed {len(movies)} movies from the Lua file")
    
    # Show some examples
    print("\n=== First 5 movies with translations ===")
    for i, movie in enumerate(movies[:5]):
        print(f"{i+1}. {movie['english_name']}")
        for lang, translation in movie['translations'].items():
            print(f"   {lang}: {translation}")
        print()
    
    # Get Cantonese movies
    cantonese_movies = parser.get_cantonese_names()
    print(f"\n=== Found {len(cantonese_movies)} movies with Cantonese translations ===")
    
    # Show some Cantonese examples
    print("First 10 English-Cantonese pairs:")
    for i, (english, cantonese) in enumerate(cantonese_movies[:10]):
        print(f"{i+1}. {english} → {cantonese}")
    
    # Save data
    parser.save_to_json('movies_all_translations.json')
    parser.save_cantonese_mapping('movies_english_cantonese.json')
    
    print(f"\nData saved to:")
    print(f"- movies_all_translations.json ({len(movies)} movies with all translations)")
    print(f"- movies_english_cantonese.json ({len(cantonese_movies)} English-Cantonese pairs)")


if __name__ == "__main__":
    main()
