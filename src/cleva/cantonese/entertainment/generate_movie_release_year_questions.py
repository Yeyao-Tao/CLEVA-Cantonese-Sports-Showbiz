#!/usr/bin/env python3
"""
Generate multiple-choice questions about movie release years.

This script uses the extracted movie release year data to create benchmark questions
for testing LLM understanding of Cantonese movie terminology and film information.
"""

import json
import random
import os
import sys
from typing import List, Dict, Any, Tuple
from datetime import datetime
import collections

# Add the project root to the Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from src.cleva.cantonese.utils.path_utils import get_entertainment_intermediate_dir, get_entertainment_output_dir
except ImportError:
    # Fallback if imports don't work
    get_entertainment_intermediate_dir = None
    get_entertainment_output_dir = None


def load_release_year_data(file_path: str) -> Dict[str, Any]:
    """Load the complete movie release year data."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_release_year_distribution(all_data: Dict[str, Any]) -> Dict[int, int]:
    """Get the distribution of release years for generating distractors."""
    movies = all_data.get('movies', {})
    release_years = []
    
    for movie_data in movies.values():
        release_year = movie_data.get('release_year')
        if release_year:
            release_years.append(release_year)
    
    return collections.Counter(release_years)


def generate_release_year_distractors(correct_year: int, year_distribution: Dict[int, int], num_distractors: int = 3) -> List[int]:
    """Generate plausible release year distractors."""
    # Get all available years except the correct one
    available_years = [year for year in year_distribution.keys() if year != correct_year]
    
    if len(available_years) < num_distractors:
        # If we don't have enough actual years, generate some nearby years
        nearby_years = []
        for offset in [1, -1, 2, -2, 3, -3, 4, -4, 5, -5]:
            candidate = correct_year + offset
            if candidate not in [correct_year] + available_years and 1950 <= candidate <= 2025:
                nearby_years.append(candidate)
        available_years.extend(nearby_years[:num_distractors - len(available_years)])
    
    # Prefer years that are close to the correct year and actually exist in our data
    def year_score(year):
        # Score based on closeness to correct year and frequency in data
        distance_penalty = abs(year - correct_year)
        frequency_bonus = year_distribution.get(year, 0) * 0.1
        return -distance_penalty + frequency_bonus
    
    available_years.sort(key=year_score, reverse=True)
    return available_years[:num_distractors]


def generate_release_year_question(movie_id: str, movie_data: Dict[str, Any], 
                                 year_distribution: Dict[int, int]) -> Dict[str, Any]:
    """Generate a multiple-choice question about a movie's release year."""
    
    movie_names = movie_data.get('movie_names', {})
    movie_name = movie_names.get('english', 'Unknown Movie')
    cantonese_name = movie_names.get('cantonese_best', movie_name)
    release_year = movie_data.get('release_year')
    release_date = movie_data.get('release_date', '')
    
    if not release_year:
        return None
    
    # Generate distractors
    distractors = generate_release_year_distractors(release_year, year_distribution)
    
    if len(distractors) < 3:
        return None  # Not enough distractors available
    
    # Create answer choices
    all_choices = [release_year] + distractors
    random.shuffle(all_choices)
    
    # Find the correct answer index
    correct_index = all_choices.index(release_year)
    correct_letter = ['A', 'B', 'C', 'D'][correct_index]
    
    question_data = {
        'question': f"What year was the movie \"{movie_name}\" released?",
        'question_cantonese': f"電影《{cantonese_name}》係邊年上映？",
        'choices': {
            'A': str(all_choices[0]),
            'B': str(all_choices[1]), 
            'C': str(all_choices[2]),
            'D': str(all_choices[3])
        },
        'choices_cantonese': {
            'A': f"{all_choices[0]}年",
            'B': f"{all_choices[1]}年", 
            'C': f"{all_choices[2]}年",
            'D': f"{all_choices[3]}年"
        },
        'correct_answer': correct_letter,
        'correct_release_info': {
            'release_year': release_year,
            'release_date': release_date
        },
        'movie_info': {
            'name': movie_name,
            'name_cantonese': cantonese_name,
            'id': movie_id
        },
        'distractors': [str(d) for d in distractors],
        'question_type': 'movie_release_year'
    }
    
    return question_data


def generate_decade_question(all_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate questions about which movie was released in a specific decade."""
    
    movies = all_data.get('movies', {})
    movies_with_dates = []
    
    for movie_id, movie_data in movies.items():
        release_year = movie_data.get('release_year')
        if release_year:
            decade = (release_year // 10) * 10  # Get decade (e.g., 2000 for 2005)
            movies_with_dates.append((movie_id, movie_data, decade))
    
    if len(movies_with_dates) < 4:
        return None
    
    # Group movies by decade
    movies_by_decade = {}
    for movie_id, movie_data, decade in movies_with_dates:
        if decade not in movies_by_decade:
            movies_by_decade[decade] = []
        movies_by_decade[decade].append((movie_id, movie_data))
    
    # Select a decade with enough movies
    valid_decades = [decade for decade, movies in movies_by_decade.items() if len(movies) >= 1]
    if not valid_decades:
        return None
    
    target_decade = random.choice(valid_decades)
    target_movie_id, target_movie_data = random.choice(movies_by_decade[target_decade])
    
    # Generate distractors from other decades
    distractor_movies = []
    for decade, movies in movies_by_decade.items():
        if decade != target_decade:
            distractor_movies.extend(movies)
    
    if len(distractor_movies) < 3:
        return None
    
    distractors = random.sample(distractor_movies, 3)
    
    # Create answer choices
    all_choices = [target_movie_data] + [movie_data for _, movie_data in distractors]
    random.shuffle(all_choices)
    
    # Find the correct answer index
    correct_index = all_choices.index(target_movie_data)
    correct_letter = ['A', 'B', 'C', 'D'][correct_index]
    
    decade_end = target_decade + 9
    
    question_data = {
        'question': f"Which of the following movies was released in the {target_decade}s ({target_decade}-{decade_end})?",
        'question_cantonese': f"以下邊套電影係喺{target_decade}年代（{target_decade}-{decade_end}年）上映？",
        'choices': {
            'A': all_choices[0]['movie_names']['english'],
            'B': all_choices[1]['movie_names']['english'],
            'C': all_choices[2]['movie_names']['english'],
            'D': all_choices[3]['movie_names']['english']
        },
        'choices_cantonese': {
            'A': f"《{all_choices[0]['movie_names']['cantonese_best']}》",
            'B': f"《{all_choices[1]['movie_names']['cantonese_best']}》",
            'C': f"《{all_choices[2]['movie_names']['cantonese_best']}》",
            'D': f"《{all_choices[3]['movie_names']['cantonese_best']}》"
        },
        'correct_answer': correct_letter,
        'correct_release_info': {
            'decade': target_decade,
            'release_year': target_movie_data['release_year'],
            'release_date': target_movie_data.get('release_date', '')
        },
        'movie_info': {
            'name': target_movie_data['movie_names']['english'],
            'name_cantonese': target_movie_data['movie_names']['cantonese_best'],
            'id': target_movie_id
        },
        'distractors': [movie_data['movie_names']['english'] for _, movie_data in distractors],
        'question_type': 'movie_decade'
    }
    
    return question_data


def generate_earliest_latest_question(all_data: Dict[str, Any], question_type: str) -> Dict[str, Any]:
    """Generate questions about the earliest or latest movie among a random sample."""
    
    movies = all_data.get('movies', {})
    movies_with_dates = []
    
    for movie_id, movie_data in movies.items():
        release_year = movie_data.get('release_year')
        if release_year:
            movies_with_dates.append((movie_id, movie_data, release_year))
    
    if len(movies_with_dates) < 4:
        return None
    
    # Select 4 random movies
    selected_movies = random.sample(movies_with_dates, 4)
    
    # Sort by release year
    selected_movies.sort(key=lambda x: x[2])  # Sort by release year
    
    if question_type == 'movie_earliest':
        target_movie_id, target_movie_data, target_year = selected_movies[0]  # Earliest
        question_text = "Which of the following movies was released earliest?"
        question_cantonese = "以下邊套電影最早上映？"
    else:  # movie_latest
        target_movie_id, target_movie_data, target_year = selected_movies[-1]  # Latest
        question_text = "Which of the following movies was released latest?"
        question_cantonese = "以下邊套電影最遲上映？"
    
    # Create answer choices (randomize order)
    all_movie_data = [movie_data for _, movie_data, _ in selected_movies]
    random.shuffle(all_movie_data)
    
    # Find the correct answer index
    correct_index = all_movie_data.index(target_movie_data)
    correct_letter = ['A', 'B', 'C', 'D'][correct_index]
    
    distractors = [movie_data['movie_names']['english'] for movie_data in all_movie_data if movie_data != target_movie_data]
    
    question_data = {
        'question': question_text,
        'question_cantonese': question_cantonese,
        'choices': {
            'A': all_movie_data[0]['movie_names']['english'],
            'B': all_movie_data[1]['movie_names']['english'],
            'C': all_movie_data[2]['movie_names']['english'],
            'D': all_movie_data[3]['movie_names']['english']
        },
        'choices_cantonese': {
            'A': f"《{all_movie_data[0]['movie_names']['cantonese_best']}》",
            'B': f"《{all_movie_data[1]['movie_names']['cantonese_best']}》",
            'C': f"《{all_movie_data[2]['movie_names']['cantonese_best']}》",
            'D': f"《{all_movie_data[3]['movie_names']['cantonese_best']}》"
        },
        'correct_answer': correct_letter,
        'correct_release_info': {
            'release_year': target_year,
            'release_date': target_movie_data.get('release_date', ''),
            'comparison_movies': [
                {
                    'name': movie_data['movie_names']['english'],
                    'release_year': release_year
                }
                for _, movie_data, release_year in selected_movies
            ]
        },
        'movie_info': {
            'name': target_movie_data['movie_names']['english'],
            'name_cantonese': target_movie_data['movie_names']['cantonese_best'],
            'id': target_movie_id
        },
        'distractors': distractors,
        'question_type': question_type
    }
    
    return question_data


def generate_all_questions(file_path: str) -> Dict[str, Any]:
    """Generate all types of movie release year questions."""
    print(f"Loading data from: {file_path}")
    all_data = load_release_year_data(file_path)
    
    movies = all_data.get('movies', {})
    print(f"Found {len(movies)} movies with release year data")
    
    if len(movies) < 4:
        print("ERROR: Not enough movies to generate meaningful questions")
        return None
    
    year_distribution = get_release_year_distribution(all_data)
    print(f"Year distribution: {len(year_distribution)} unique years")
    
    all_questions = []
    question_type_counts = {
        'movie_release_year': 0,
        'movie_decade': 0,
        'movie_earliest': 0,
        'movie_latest': 0
    }
    
    # Generate release year questions for each movie
    print("Generating release year questions...")
    for movie_id, movie_data in movies.items():
        question = generate_release_year_question(movie_id, movie_data, year_distribution)
        if question:
            all_questions.append(question)
            question_type_counts['movie_release_year'] += 1
    
    # Generate decade questions
    print("Generating decade questions...")
    for i in range(min(50, len(movies) // 2)):  # Generate up to 50 decade questions
        question = generate_decade_question(all_data)
        if question:
            all_questions.append(question)
            question_type_counts['movie_decade'] += 1
    
    # Generate earliest/latest questions
    print("Generating earliest/latest questions...")
    for i in range(min(25, len(movies) // 4)):  # Generate up to 25 each
        earliest_question = generate_earliest_latest_question(all_data, 'movie_earliest')
        if earliest_question:
            all_questions.append(earliest_question)
            question_type_counts['movie_earliest'] += 1
        
        latest_question = generate_earliest_latest_question(all_data, 'movie_latest')
        if latest_question:
            all_questions.append(latest_question)
            question_type_counts['movie_latest'] += 1
    
    # Shuffle all questions
    random.shuffle(all_questions)
    
    # Create output structure matching soccer questions
    output_data = {
        'metadata': {
            'description': 'Multiple-choice questions about movie release years and chronology in English and Cantonese',
            'purpose': 'Cantonese benchmark for testing LLM understanding of movie information and chronology',
            'question_types': list(question_type_counts.keys()),
            'question_type_distribution': question_type_counts,
            'languages': ['English', 'Cantonese'],
            'total_questions': len(all_questions),
            'generation_date': datetime.now().isoformat(),
            'format': 'Four choices (A, B, C, D) with one correct answer in both languages'
        },
        'questions': all_questions
    }
    
    print(f"Generated {len(all_questions)} total questions:")
    for q_type, count in question_type_counts.items():
        print(f"  {q_type}: {count}")
    
    return output_data


def main():
    """Main function to generate movie release year questions."""
    # Set random seed for reproducible results
    random.seed(42)
    
    # Get input and output paths
    if get_entertainment_intermediate_dir and get_entertainment_output_dir:
        try:
            intermediate_dir = get_entertainment_intermediate_dir()
            output_dir = get_entertainment_output_dir()
        except:
            # Fallback to relative paths if utils are not available
            current_dir = os.path.dirname(os.path.abspath(__file__))
            repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
            intermediate_dir = os.path.join(repo_root, 'data', 'entertainment', 'intermediate')
            output_dir = os.path.join(repo_root, 'data', 'entertainment', 'output')
    else:
        # Fallback to relative paths if utils are not available
        current_dir = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
        intermediate_dir = os.path.join(repo_root, 'data', 'entertainment', 'intermediate')
        output_dir = os.path.join(repo_root, 'data', 'entertainment', 'output')
    
    input_file = os.path.join(intermediate_dir, 'movies_release_years.json')
    output_file = os.path.join(output_dir, 'movie_release_year_questions.json')
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    print("=== Movie Release Year Questions Generator ===")
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"ERROR: Input file not found: {input_file}")
        sys.exit(1)
    
    # Generate questions
    questions_data = generate_all_questions(input_file)
    
    if not questions_data:
        print("ERROR: Failed to generate questions")
        sys.exit(1)
    
    # Save to output file
    print(f"Saving questions to: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(questions_data, f, ensure_ascii=False, indent=2)
    
    print("✅ Questions generated successfully!")
    print(f"Total questions: {questions_data['metadata']['total_questions']}")


if __name__ == '__main__':
    main()