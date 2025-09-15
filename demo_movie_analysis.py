#!/usr/bin/env python3
"""
Demo: Working with Lua Movie Data

This script demonstrates different ways to work with the parsed movie data.
"""

import json
import re


def load_movie_data():
    """Load the parsed movie data."""
    # Load all translations
    with open('movies_simple_all.json', 'r', encoding='utf-8') as f:
        all_movies = json.load(f)
    
    # Load just English-Cantonese pairs
    with open('movies_simple_cantonese.json', 'r', encoding='utf-8') as f:
        cantonese_movies = json.load(f)
    
    return all_movies, cantonese_movies


def search_movies_by_keyword(movies_dict, keyword, search_in='english'):
    """
    Search for movies containing a keyword.
    
    Args:
        movies_dict: Dictionary of movie data
        keyword: Keyword to search for
        search_in: 'english', 'cantonese', or 'both'
    """
    results = []
    keyword_lower = keyword.lower()
    
    if search_in in ['english', 'both']:
        # Search in English names
        for english_name in movies_dict:
            if keyword_lower in english_name.lower():
                results.append(english_name)
    
    if search_in in ['cantonese', 'both']:
        # Search in Cantonese names
        for english_name, cantonese_name in movies_dict.items():
            if isinstance(cantonese_name, str) and keyword in cantonese_name:
                results.append(f"{english_name} ({cantonese_name})")
    
    return results


def get_movies_by_year_pattern(movies_dict, year_pattern):
    """Find movies with years in their titles."""
    results = []
    
    for english_name in movies_dict:
        if re.search(year_pattern, english_name):
            results.append(english_name)
    
    return results


def analyze_translation_patterns(all_movies):
    """Analyze common patterns in translations."""
    
    # Count available language variants
    lang_counts = {}
    for movie, translations in all_movies.items():
        for lang_code in translations:
            lang_counts[lang_code] = lang_counts.get(lang_code, 0) + 1
    
    print("=== Language Variant Statistics ===")
    for lang_code, count in sorted(lang_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"{lang_code}: {count} movies")
    
    return lang_counts


def main():
    """Demonstrate various ways to work with the movie data."""
    
    print("Loading movie data...")
    all_movies, cantonese_movies = load_movie_data()
    
    print(f"Loaded {len(all_movies)} movies with translations")
    print(f"Loaded {len(cantonese_movies)} English-Cantonese pairs\n")
    
    # 1. Search examples
    print("=== Search Examples ===")
    
    # Search for movies with "Star" in the title
    star_movies = search_movies_by_keyword(cantonese_movies, "Star", "english")
    print(f"Movies with 'Star' in English title ({len(star_movies)} found):")
    for movie in star_movies[:5]:  # Show first 5
        cantonese = cantonese_movies.get(movie, "No Cantonese translation")
        print(f"  {movie} → {cantonese}")
    
    print()
    
    # Search for movies with specific Chinese characters
    love_movies = search_movies_by_keyword(cantonese_movies, "愛", "cantonese")
    print(f"Movies with '愛' in Cantonese title ({len(love_movies)} found):")
    for movie in love_movies[:5]:  # Show first 5
        print(f"  {movie}")
    
    print()
    
    # 2. Year-based search
    print("=== Movies with Years in Titles ===")
    year_movies = get_movies_by_year_pattern(cantonese_movies, r'\b(19|20)\d{2}\b')
    print(f"Found {len(year_movies)} movies with years in titles:")
    for movie in year_movies[:10]:  # Show first 10
        cantonese = cantonese_movies.get(movie, "No Cantonese")
        print(f"  {movie} → {cantonese}")
    
    print()
    
    # 3. Translation analysis
    analyze_translation_patterns(all_movies)
    
    print()
    
    # 4. Specific movie lookup
    print("=== Specific Movie Examples ===")
    test_movies = ["Titanic", "Avatar", "The Lion King", "Frozen", "Spider-Man"]
    
    for movie in test_movies:
        if movie in all_movies:
            print(f"\n{movie}:")
            for lang_code, translation in all_movies[movie].items():
                print(f"  {lang_code}: {translation}")
        else:
            print(f"\n{movie}: Not found in database")
    
    print()
    
    # 5. Export specific subsets
    print("=== Export Examples ===")
    
    # Export movies from a specific decade
    movies_2010s = {}
    for english_name, cantonese_name in cantonese_movies.items():
        if re.search(r'\b201\d\b', english_name):  # Movies with 2010-2019 in title
            movies_2010s[english_name] = cantonese_name
    
    if movies_2010s:
        with open('movies_2010s.json', 'w', encoding='utf-8') as f:
            json.dump(movies_2010s, f, ensure_ascii=False, indent=2)
        print(f"Exported {len(movies_2010s)} movies from 2010s to movies_2010s.json")
    
    # Export superhero movies (simple keyword search)
    superhero_keywords = ['Spider', 'Batman', 'Superman', 'Iron Man', 'Captain', 'Thor', 'Avengers']
    superhero_movies = {}
    
    for english_name, cantonese_name in cantonese_movies.items():
        for keyword in superhero_keywords:
            if keyword.lower() in english_name.lower():
                superhero_movies[english_name] = cantonese_name
                break
    
    if superhero_movies:
        with open('movies_superhero.json', 'w', encoding='utf-8') as f:
            json.dump(superhero_movies, f, ensure_ascii=False, indent=2)
        print(f"Exported {len(superhero_movies)} superhero movies to movies_superhero.json")


if __name__ == "__main__":
    main()
