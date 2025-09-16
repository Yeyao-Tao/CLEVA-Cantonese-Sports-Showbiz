#!/usr/bin/env python3
"""
Extract movie release years from WikiData JSONLD files.

This script reads JSONLD files from data/entertainment/intermediate/movie_triples/
and extracts release year information for each movie, following the schema pattern
used in data/soccer/intermediate/players_birth_years.json.
"""

import json
import os
from datetime import datetime
from pathlib import Path

from cleva.cantonese.utils.path_utils import (
    get_entertainment_intermediate_dir, 
    get_movies_triples_dir
)


def extract_movie_data(jsonld_file_path):
    """
    Extract movie data from a JSONLD file.
    
    Args:
        jsonld_file_path (str): Path to the JSONLD file
        
    Returns:
        dict or None: Movie data dictionary or None if extraction fails
    """
    try:
        with open(jsonld_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Find the main movie entity in the @graph
        movie_entity = None
        movie_qid = os.path.basename(jsonld_file_path).replace('.jsonld', '')
        
        for item in data.get('@graph', []):
            if item.get('@id') == f'wd:{movie_qid}' and 'P577' in item:
                movie_entity = item
                break
        
        if not movie_entity:
            print(f"Warning: No movie entity found for {movie_qid}")
            return None
        
        # Extract release dates from P577 property
        release_dates = movie_entity.get('P577', [])
        if not release_dates:
            print(f"Warning: No release dates found for {movie_qid}")
            return None
        
        # Filter out invalid dates and get the earliest valid release date
        valid_dates = [date for date in release_dates if not date.startswith('-')]
        if not valid_dates:
            print(f"Warning: No valid release dates found for {movie_qid}")
            return None
        
        earliest_date = min(valid_dates)
        release_year = int(earliest_date[:4])  # Extract year from "YYYY-MM-DDTHH:MM:SSZ" format
        
        # Extract English title
        english_title = None
        p1476_title = movie_entity.get('P1476')
        if p1476_title and isinstance(p1476_title, dict):
            if p1476_title.get('@language') == 'en':
                english_title = p1476_title.get('@value')
        
        # If no P1476 English title, look for labels in the graph
        if not english_title:
            for item in data.get('@graph', []):
                if item.get('@id') == f'wd:{movie_qid}' and 'label' in item:
                    labels = item.get('label', [])
                    if isinstance(labels, list):
                        for label in labels:
                            if label.get('@language') == 'en':
                                english_title = label.get('@value')
                                break
                    elif isinstance(labels, dict) and labels.get('@language') == 'en':
                        english_title = labels.get('@value')
                    break
        
        # Extract Cantonese titles (yue and zh-hk)
        cantonese_titles = {}
        cantonese_best = None
        cantonese_lang = None
        
        # Look for labels in all items in the graph
        for item in data.get('@graph', []):
            if item.get('@id') == f'wd:{movie_qid}' and 'label' in item:
                labels = item.get('label', [])
                if isinstance(labels, list):
                    for label in labels:
                        lang = label.get('@language')
                        value = label.get('@value')
                        if lang in ['yue', 'zh-hk'] and value:
                            cantonese_titles[lang] = value
                            # Prefer yue over zh-hk
                            if lang == 'yue':
                                cantonese_best = value
                                cantonese_lang = 'yue'
                            elif lang == 'zh-hk' and not cantonese_best:
                                cantonese_best = value
                                cantonese_lang = 'zh-hk'
                break
        
        # Build movie data structure
        movie_data = {
            'movie_id': movie_qid,
            'movie_names': {
                'id': movie_qid,
                'english': english_title,
                'cantonese': cantonese_titles,
                'cantonese_best': cantonese_best,
                'cantonese_lang': cantonese_lang,
                'cantonese_source': 'wikidata'
            },
            'release_date': earliest_date,
            'release_year': release_year,
            'all_release_dates': valid_dates,
            'file_path': str(jsonld_file_path),
            'has_cantonese_data': bool(cantonese_titles),
            'has_release_data': True
        }
        
        return movie_data
    
    except Exception as e:
        print(f"Error processing {jsonld_file_path}: {e}")
        return None


def main():
    """
    Main function to process all movie JSONLD files and generate the output.
    """
    # Set up paths
    base_dir = Path(__file__).parent
    movie_triples_dir = get_movies_triples_dir()
    output_file = get_entertainment_intermediate_dir() + '/movies_release_years.json'
    
    # Get all JSONLD files
    jsonld_files = list(Path(movie_triples_dir).glob('*.jsonld'))
    
    print(f"Found {len(jsonld_files)} JSONLD files to process")
    
    # Process each file
    movies = {}
    processed_count = 0
    error_count = 0
    movies_with_cantonese = 0
    
    start_time = datetime.now()
    
    for jsonld_file in jsonld_files:
        movie_data = extract_movie_data(jsonld_file)
        if movie_data:
            movies[movie_data['movie_id']] = movie_data
            processed_count += 1
            if movie_data['has_cantonese_data']:
                movies_with_cantonese += 1
        else:
            error_count += 1
        
        # Progress indicator
        if (processed_count + error_count) % 10 == 0:
            print(f"Processed {processed_count + error_count}/{len(jsonld_files)} files...")
    
    end_time = datetime.now()
    processing_time = (end_time - start_time).total_seconds()
    
    # Create output structure similar to players_birth_years.json
    output_data = {
        'metadata': {
            'description': 'Movie release years extracted from WikiData for analysis and benchmark construction',
            'purpose': 'Support generation of questions about movie release years and decade analysis',
            'data_structure': {
                'movies': 'Dictionary of movie_id -> movie data with release year information',
                'note': 'Only includes movies with valid release year data'
            },
            'extraction_date': datetime.now().isoformat(),
            'total_movies_with_release_data': processed_count,
            'total_movies_with_cantonese_data': movies_with_cantonese,
            'processing_time_seconds': round(processing_time, 2),
            'performance_optimization': 'Direct JSONLD parsing for improved speed',
            'filtering_info': {
                'original_movie_count': len(jsonld_files),
                'filtered_movie_count': processed_count,
                'error_count': error_count,
                'filtering_ratio': round((processed_count / len(jsonld_files)) * 100, 1) if jsonld_files else 0,
                'filter_criteria': 'Movies must have valid release year data (P577 property)'
            }
        },
        'movies': movies
    }
    
    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nProcessing complete!")
    print(f"Successfully processed: {processed_count} movies")
    print(f"Movies with Cantonese data: {movies_with_cantonese}")
    print(f"Errors: {error_count}")
    print(f"Processing time: {processing_time:.2f} seconds")
    print(f"Output saved to: {output_file}")


if __name__ == '__main__':
    main()