#!/usr/bin/env python3
"""
Movie specific Wikidata lookup script.

This script uses the generic wikidata_lookup module to resolve
movie names to Wikidata Q-IDs and fetch their JSON-LD data.

Reads from movies_simple_english_cantonese.json which contains
mappings of English movie titles to Cantonese titles.

Filters for movies specifically by requiring:
  - P31 (instance of) includes Q11424 (film)

The script filters for Cantonese labels during the data fetching process,
only saving JSON-LD files for movies that have Cantonese (yue) or Hong Kong Chinese (zh-hk) labels.

Requires: requests
"""
import os
import sys
import json
import random

# Add the parent directory to the path to import the generic wikidata_lookup module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wikidata_lookup import (
    resolve_entity_qids, 
    fetch_all_entity_triples,
    create_entity_filter
)
from utils.path_utils import (
    get_movies_triples_dir, 
    get_entertainment_intermediate_dir
)

# Path constants
TRIPLES_DIR = get_movies_triples_dir() + "/"

# Configuration constants
MAX_MOVIES_TO_PROCESS = 400

def read_movie_names_from_json(file_path):
    """
    Read movie names from the JSON file containing English to Cantonese mappings.
    
    Args:
        file_path (str): Path to the JSON file
        
    Returns:
        list: List of English movie names
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Movie names file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        movie_mappings = json.load(f)
    
    # Extract English names (keys)
    english_names = list(movie_mappings.keys())
    return english_names

def main():
    """Main function to resolve movie Q-IDs and fetch their data."""
    # Read movie names from the English-Cantonese mapping file
    movies_file = os.path.join(get_entertainment_intermediate_dir(), "movies_simple_english_cantonese.json")
    
    try:
        movie_names = read_movie_names_from_json(movies_file)
        print(f"Loaded {len(movie_names)} movie names from {movies_file}")
        print("Starting movie Q-ID resolution...\n")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure the movies_simple_english_cantonese.json file exists.")
        exit(1)
    
    # Create movie filter
    movie_filter = create_entity_filter("movie")
    
    # Set fixed seed for deterministic random selection
    random.seed(42)
    
    # Randomly select movies instead of taking the first ones
    total_movies = len(movie_names)
    if total_movies > MAX_MOVIES_TO_PROCESS:
        movie_names = random.sample(movie_names, MAX_MOVIES_TO_PROCESS)
        print(f"Randomly selected {MAX_MOVIES_TO_PROCESS} movies out of {total_movies} total movies")
    else:
        print(f"Processing all {total_movies} movies (less than {MAX_MOVIES_TO_PROCESS})")
    
    # Resolve Q-IDs for all movies
    mapping, filtered = resolve_entity_qids(movie_names, movie_filter)

    print("\n" + "="*50)
    print("RESOLUTION COMPLETE - RESULTS:")
    print("="*50)
    
    resolved_count = len([qid for qid in mapping.values() if qid])
    print(f"Movies with Q-IDs found: {resolved_count}/{len(movie_names)}")
    
    print("\nResolved mapping (first 10):")
    for idx, (nm, qid) in enumerate(mapping.items()):
        if idx >= 10:  # Only show first 10 to avoid overwhelming output
            break
        status = "✓" if qid else "✗"
        print(f"  {status} {nm} -> {qid}")
    
    if len(mapping) > 10:
        print(f"  ... and {len(mapping) - 10} more")

    print("\nFiltered-out candidates (not movies):")
    filtered_count = 0
    for nm, qids in filtered.items():
        if qids:
            if filtered_count < 5:  # Only show first 5 to avoid overwhelming output
                print(f"  {nm}: {', '.join(qids)}")
            filtered_count += 1
    if filtered_count > 5:
        print(f"  ... and {filtered_count - 5} more movies with filtered candidates")

    # Fetch JSON-LD triples for all resolved movies and filter for Cantonese labels
    saved_files, movies_with_cantonese, movies_without_cantonese = fetch_all_entity_triples(
        mapping, 
        TRIPLES_DIR, 
        filter_cantonese=True,
        entity_type="movie"
    )
    
    print(f"\n" + "="*50)
    print("FINAL SUMMARY:")
    print("="*50)
    print(f"- Total movies processed: {len(movie_names)}")
    print(f"- Movies with Q-IDs found: {resolved_count}")
    print(f"- Movies with Cantonese labels: {len(movies_with_cantonese)}")
    print(f"- Movies without Cantonese labels: {len(movies_without_cantonese)}")
    print(f"- JSON-LD files saved: {len(saved_files)} (only for movies with Cantonese labels)")
    print(f"- Files saved to: {TRIPLES_DIR}")
    
    if movies_with_cantonese:
        print(f"\nFirst 10 movies with Cantonese labels:")
        for idx, (qid, name) in enumerate(movies_with_cantonese.items()):
            if idx >= 10:  # Only show first 10
                break
            print(f"  - {name} ({qid})")
        if len(movies_with_cantonese) > 10:
            print(f"  ... and {len(movies_with_cantonese) - 10} more")
    
    # Save the list of movies with Cantonese labels to a file
    cantonese_movies_file = os.path.join(get_entertainment_intermediate_dir(), "movies_with_cantonese_labels.txt")
    with open(cantonese_movies_file, 'w', encoding='utf-8') as f:
        for qid in movies_with_cantonese:
            f.write(f"{qid}\n")
    print(f"\nList of movies with Cantonese labels saved to: {cantonese_movies_file}")
    
    # Save the mapping of Q-IDs to movie names for movies with Cantonese labels
    qid_name_mapping_file = os.path.join(get_entertainment_intermediate_dir(), "movies_cantonese_qid_mapping.json")
    with open(qid_name_mapping_file, 'w', encoding='utf-8') as f:
        json.dump(movies_with_cantonese, f, indent=2, ensure_ascii=False)
    print(f"Q-ID to name mapping for movies with Cantonese labels saved to: {qid_name_mapping_file}")

if __name__ == "__main__":
    main()
