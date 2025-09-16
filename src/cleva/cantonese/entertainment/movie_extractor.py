#!/usr/bin/env python3
"""
Movie Name Extractor

This script reads the cgroup_movie.lua file and extracts English and Cantonese (zh-hk) 
movie names, filtering out non-movie items based on content sections.

The script identifies movie entries using the Item() function calls and stops processing
when it encounters non-movie sections like film festivals, studios, and technical terms.

Outputs both detailed and simple JSON formats in a single run.
"""

import re
import json
import os
from typing import List, Dict, Optional, Tuple


class MovieExtractor:
    """Extracts movie names from MediaWiki CGroup Lua files."""
    
    def __init__(self, lua_file_path: str):
        self.lua_file_path = lua_file_path
        self.movies = []
        
        # Section markers that indicate non-movie content
        self.non_movie_sections = [
            '==獎項、電影節==',
            '==虛構角色==',
            '==電影節及相關獎項==',
            '==製片廠及相關業者==', 
            '==其他==',
            '==繁簡轉換=='
        ]
    
    def extract_cantonese_name(self, conversion_rules: str) -> Optional[str]:
        """
        Extract Cantonese name from zh-hk conversion rules.
        
        Args:
            conversion_rules: String containing conversion rules like 'zh-tw:title;zh-hk:title;zh-cn:title;'
        
        Returns:
            Cantonese name if found, None otherwise
        """
        # Look for zh-hk: followed by the Cantonese name
        zh_hk_pattern = r'zh-hk:([^;]+)'
        match = re.search(zh_hk_pattern, conversion_rules)
        
        if match:
            cantonese_name = match.group(1).strip()
            # Remove any trailing punctuation
            cantonese_name = re.sub(r'[;,]+$', '', cantonese_name)
            return cantonese_name
        
        return None
    
    def parse_item_line(self, line: str) -> Optional[Tuple[str, str]]:
        """
        Parse an Item() line to extract English and Cantonese names.
        
        Args:
            line: Line from the lua file containing an Item() call
            
        Returns:
            Tuple of (english_name, cantonese_name) if both found, None otherwise
        """
        # Pattern to match Item('English Name', 'conversion rules')
        item_pattern = r"Item\s*\(\s*['\"]([^'\"]+)['\"],\s*['\"]([^'\"]+)['\"]"
        
        match = re.search(item_pattern, line)
        if not match:
            return None
            
        english_name = match.group(1).strip()
        conversion_rules = match.group(2).strip()
        
        # Skip if no English name
        if not english_name:
            return None
            
        # Extract Cantonese name
        cantonese_name = self.extract_cantonese_name(conversion_rules)
        
        # Only return if we have both names
        if english_name and cantonese_name:
            return (english_name, cantonese_name)
        
        return None
    
    def is_non_movie_section(self, line: str) -> bool:
        """Check if line indicates start of non-movie section."""
        for section_marker in self.non_movie_sections:
            if section_marker in line:
                return True
        return False
    
    def extract_movies(self) -> List[Dict[str, str]]:
        """
        Extract all movie entries from the lua file.
        
        Returns:
            List of dictionaries with 'english_name' and 'cantonese_name' keys
        """
        movies = []
        
        try:
            with open(self.lua_file_path, 'r', encoding='utf-8') as file:
                for line_num, line in enumerate(file, 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('--'):
                        continue
                    
                    # Check if we've reached non-movie sections
                    if self.is_non_movie_section(line):
                        print(f"Stopping at line {line_num}: Found non-movie section")
                        break
                    
                    # Skip text type entries (section headers)
                    if 'type = \'text\'' in line or 'type = "text"' in line:
                        continue
                    
                    # Try to parse Item() entries
                    if line.strip().startswith('Item('):
                        result = self.parse_item_line(line)
                        if result:
                            english_name, cantonese_name = result
                            movie_entry = {
                                'english_name': english_name,
                                'cantonese_name': cantonese_name,
                                'line_number': line_num
                            }
                            movies.append(movie_entry)
                            print(f"Extracted: {english_name} -> {cantonese_name}")
        
        except FileNotFoundError:
            print(f"Error: File not found: {self.lua_file_path}")
            return []
        except Exception as e:
            print(f"Error reading file: {e}")
            return []
        
        self.movies = movies
        return movies
    
    def save_to_json(self, detailed_output_path: str, simple_output_path: str) -> Tuple[bool, bool]:
        """
        Save extracted movies to both detailed and simple JSON formats.
        
        Args:
            detailed_output_path: Path to detailed JSON file with metadata
            simple_output_path: Path to simple key-value JSON file
            
        Returns:
            Tuple of (detailed_success, simple_success)
        """
        detailed_success = False
        simple_success = False
        
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(detailed_output_path), exist_ok=True)
            os.makedirs(os.path.dirname(simple_output_path), exist_ok=True)
            
            # Save detailed format
            metadata = {
                'source_file': self.lua_file_path,
                'total_movies': len(self.movies),
                'extraction_info': 'Movies with both English and Cantonese (zh-hk) names',
                'movies': self.movies
            }
            
            with open(detailed_output_path, 'w', encoding='utf-8') as file:
                json.dump(metadata, file, ensure_ascii=False, indent=2)
            
            print(f"Successfully saved detailed format with {len(self.movies)} movies to {detailed_output_path}")
            detailed_success = True
            
            # Save simple format
            simple_movies = {}
            for movie in self.movies:
                simple_movies[movie['english_name']] = movie['cantonese_name']
            
            with open(simple_output_path, 'w', encoding='utf-8') as file:
                json.dump(simple_movies, file, ensure_ascii=False, indent=2)
            
            print(f"Successfully saved simple format with {len(simple_movies)} movies to {simple_output_path}")
            simple_success = True
            
        except Exception as e:
            print(f"Error saving to JSON: {e}")
        
        return detailed_success, simple_success


def main():
    """Main function to run the movie extractor."""
    # File paths
    lua_file = '/Users/taoyeyao/workplace/CLEVA-Cantonese-Sports-Showbiz/data/entertainment/raw/cgroup_movie.lua'
    detailed_output = '/Users/taoyeyao/workplace/CLEVA-Cantonese-Sports-Showbiz/data/entertainment/intermediate/movies_english_cantonese.json'
    simple_output = '/Users/taoyeyao/workplace/CLEVA-Cantonese-Sports-Showbiz/data/entertainment/intermediate/movies_simple_english_cantonese.json'
    
    # Create extractor and process
    extractor = MovieExtractor(lua_file)
    movies = extractor.extract_movies()
    
    if movies:
        print(f"\nExtracted {len(movies)} movies with both English and Cantonese names")
        
        # Save to both formats
        detailed_success, simple_success = extractor.save_to_json(detailed_output, simple_output)
        
        if detailed_success and simple_success:
            print("Successfully saved results in both formats")
        elif detailed_success:
            print("Detailed format saved successfully, but simple format failed")
        elif simple_success:
            print("Simple format saved successfully, but detailed format failed")
        else:
            print("Failed to save results in both formats")
    else:
        print("No movies were extracted")


if __name__ == "__main__":
    main()
