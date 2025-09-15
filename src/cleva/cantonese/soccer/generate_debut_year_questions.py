#!/usr/bin/env python3
"""
Generate multiple-choice questions about football players' national team debut years.

This script uses the extracted player-club data to create benchmark questions
for testing LLM understanding of Cantonese football terminology, specifically
focusing on when players first debuted for their senior national teams.
"""

import json
import random
import os
import sys
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

from cleva.cantonese.utils.file_utils import load_player_data
from cleva.cantonese.utils.path_utils import get_soccer_intermediate_dir, get_soccer_output_dir


def get_national_teams_only(player_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get only senior national teams for a player, excluding youth teams."""
    national_teams = []
    for team in player_data.get('national_teams', []):
        description = team.get('description', '').lower()
        name = team.get('name', '').lower()
        
        # Skip youth teams
        is_youth = any(keyword in description for keyword in ['under-', 'youth', 'u-']) or \
                   any(keyword in name for keyword in ['under-', 'youth', 'u-'])
        
        if not is_youth:
            national_teams.append(team)
            
    return national_teams


def get_earliest_national_team_debut(player_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get the earliest national team debut for a player."""
    national_teams = get_national_teams_only(player_data)
    
    if not national_teams:
        return None
    
    # Filter teams that have start_year data
    teams_with_debut = [team for team in national_teams if team.get('start_year') is not None]
    
    if not teams_with_debut:
        return None
    
    # Find the team with the earliest start year
    earliest_team = min(teams_with_debut, key=lambda x: x['start_year'])
    return earliest_team


def get_debut_years_distribution(all_data: Dict[str, Any]) -> Dict[int, int]:
    """Get distribution of debut years to create realistic distractors."""
    players = all_data.get('players', {})
    debut_years = []
    
    for player_id, player_data in players.items():
        earliest_debut = get_earliest_national_team_debut(player_data)
        if earliest_debut and earliest_debut.get('start_year'):
            debut_years.append(earliest_debut['start_year'])
    
    # Count frequency of each year
    year_counts = {}
    for year in debut_years:
        year_counts[year] = year_counts.get(year, 0) + 1
    
    return year_counts


def generate_realistic_distractor_years(correct_year: int, all_debut_years: Dict[int, int], 
                                       num_distractors: int = 3) -> List[int]:
    """Generate realistic distractor years based on actual debut year distribution."""
    # Get all available years except the correct one
    available_years = [year for year in all_debut_years.keys() if year != correct_year]
    
    if len(available_years) < num_distractors:
        # If not enough real years, generate some nearby years
        min_year = min(all_debut_years.keys()) if all_debut_years else correct_year - 10
        max_year = max(all_debut_years.keys()) if all_debut_years else correct_year + 5
        
        # Generate years within reasonable range
        nearby_years = []
        for offset in [-5, -4, -3, -2, -1, 1, 2, 3, 4, 5]:
            candidate = correct_year + offset
            if min_year <= candidate <= max_year and candidate != correct_year:
                nearby_years.append(candidate)
        
        # Combine real years with nearby years
        available_years.extend(nearby_years)
        available_years = list(set(available_years))  # Remove duplicates
    
    # Sort by how common they are (prefer more common years as distractors)
    available_years.sort(key=lambda x: all_debut_years.get(x, 0), reverse=True)
    
    # Take the top options, but randomize a bit
    if len(available_years) >= num_distractors:
        # Take top candidates but with some randomization
        top_candidates = available_years[:min(num_distractors * 2, len(available_years))]
        return random.sample(top_candidates, num_distractors)
    else:
        return available_years[:num_distractors]


def generate_debut_year_question(player_id: str, player_data: Dict[str, Any], 
                                all_debut_years: Dict[int, int]) -> Optional[Dict[str, Any]]:
    """Generate a multiple-choice question about when a player first debuted for their national team."""
    
    # Get player names
    player_names = player_data.get('player_names', {})
    player_name = player_names.get('english', 'Unknown Player')
    cantonese_name = player_names.get('cantonese_best', player_name)
    
    # Get earliest national team debut
    earliest_debut = get_earliest_national_team_debut(player_data)
    if not earliest_debut or not earliest_debut.get('start_year'):
        return None
    
    correct_year = earliest_debut['start_year']
    team_name = earliest_debut.get('name', 'Unknown Team')
    team_cantonese_name = earliest_debut.get('cantonese_name', team_name)
    
    # Generate distractor years
    distractor_years = generate_realistic_distractor_years(correct_year, all_debut_years, 3)
    
    if len(distractor_years) < 3:
        return None  # Not enough distractors available
    
    # Create answer choices
    all_years = [correct_year] + distractor_years
    random.shuffle(all_years)
    
    # Find the correct answer index
    correct_index = all_years.index(correct_year)
    correct_letter = ['A', 'B', 'C', 'D'][correct_index]
    
    # Create question text
    question_text = f"In which year did {player_name} first debut for the senior national team?"
    question_text_cantonese = f"{cantonese_name}喺邊一年首次代表成年國家隊出賽？"
    
    question_data = {
        'question': question_text,
        'question_cantonese': question_text_cantonese,
        'choices': {
            'A': str(all_years[0]),
            'B': str(all_years[1]), 
            'C': str(all_years[2]),
            'D': str(all_years[3])
        },
        'choices_cantonese': {
            'A': f"{all_years[0]}年",
            'B': f"{all_years[1]}年", 
            'C': f"{all_years[2]}年",
            'D': f"{all_years[3]}年"
        },
        'correct_answer': correct_letter,
        'debut_info': {
            'year': correct_year,
            'team_name': team_name,
            'team_name_cantonese': team_cantonese_name,
            'team_id': earliest_debut.get('club_id'),
            'is_current': earliest_debut.get('is_current', False),
            'start_date': earliest_debut.get('start_date'),
        },
        'player_info': {
            'name': player_name,
            'name_cantonese': cantonese_name,
            'id': player_id,
            'total_national_teams': len(get_national_teams_only(player_data))
        },
        'distractors': [str(year) for year in distractor_years],
        'question_type': 'player_national_team_debut_year'
    }
    
    return question_data


def generate_multiple_debut_year_questions(all_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate multiple debut year questions."""
    
    players = all_data.get('players', {})
    
    # Get debut year distribution for realistic distractors
    print("Analyzing debut year distribution...")
    all_debut_years = get_debut_years_distribution(all_data)
    print(f"Found debut years ranging from {min(all_debut_years.keys())} to {max(all_debut_years.keys())}")
    
    questions = []
    
    # Get players with national team experience and known debut years
    eligible_players = []
    for player_id, player_data in players.items():
        earliest_debut = get_earliest_national_team_debut(player_data)
        player_names = player_data.get('player_names', {})
        player_name = player_names.get('english')
        
        if earliest_debut and earliest_debut.get('start_year') and player_name:
            eligible_players.append((player_id, player_data))
    
    print(f"Found {len(eligible_players)} eligible players for debut year questions")

    for player_id, player_data in eligible_players:
        question = generate_debut_year_question(player_id, player_data, all_debut_years)
        if question:
            questions.append(question)

    return questions


def format_question_for_display(question_data: Dict[str, Any]) -> str:
    """Format a question for human-readable display."""
    
    formatted = f'"""\nEnglish: {question_data["question"]}\n'
    for letter in ['A', 'B', 'C', 'D']:
        formatted += f'{letter}. {question_data["choices"][letter]}\n'
    
    formatted += f'\nCantonese: {question_data["question_cantonese"]}\n'
    for letter in ['A', 'B', 'C', 'D']:
        formatted += f'{letter}. {question_data["choices_cantonese"][letter]}\n'
    formatted += '"""'
    
    return formatted


def save_questions(questions: List[Dict[str, Any]], output_file: str):
    """Save questions to a JSON file with metadata."""
    
    # Calculate some statistics
    debut_years = [q['debut_info']['year'] for q in questions]
    year_range = f"{min(debut_years)}-{max(debut_years)}" if debut_years else "N/A"
    
    current_teams = sum(1 for q in questions if q['debut_info']['is_current'])
    former_teams = len(questions) - current_teams
    
    output_data = {
        'metadata': {
            'description': 'Multiple-choice questions about football player national team debut years in English and Cantonese',
            'purpose': 'Cantonese benchmark for testing LLM understanding of football player career timelines',
            'question_type': 'player_national_team_debut_year',
            'languages': ['English', 'Cantonese'],
            'total_questions': len(questions),
            'year_range': year_range,
            'current_national_teams': current_teams,
            'former_national_teams': former_teams,
            'generation_date': datetime.now().isoformat(),
            'format': 'Four year choices (A, B, C, D) with one correct answer in both languages'
        },
        'questions': questions
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    # Get the data file path
    data_file = os.path.join(get_soccer_intermediate_dir(), "football_players_clubs_complete.json")
    
    print("Loading player data...")
    all_data = load_player_data(data_file)
    
    print(f"Loaded data for {len(all_data['players'])} players")
    
    # Generate questions
    print("\nGenerating debut year questions...")
    questions = generate_multiple_debut_year_questions(all_data)
    print(f"Generated {len(questions)} debut year questions")
    
    if not questions:
        print("No questions generated. Check if players have national team debut year data.")
        exit(1)
    
    # Shuffle questions
    random.shuffle(questions)
    
    print(f"\nTotal questions generated: {len(questions)}")
    
    # Save to file
    output_file = os.path.join(get_soccer_output_dir(), "debut_year_questions.json")
    
    # Ensure output directory exists
    os.makedirs(get_soccer_output_dir(), exist_ok=True)
    
    save_questions(questions, output_file)
    
    print(f"Questions saved to {output_file}")
    
    # Display first 5 questions as examples
    print("\n" + "="*80)
    print("SAMPLE QUESTIONS")
    print("="*80)
    
    for i, question in enumerate(questions[:5], 1):
        print(f"\nQuestion {i}:")
        print(format_question_for_display(question))
        print(f"Correct Answer: {question['correct_answer']}")
        
        player_info = question['player_info']
        debut_info = question['debut_info']
        
        print(f"Player: {player_info['name']} / {player_info['name_cantonese']} ({player_info['total_national_teams']} national teams)")
        print(f"Debut: {debut_info['year']} for {debut_info['team_name']} / {debut_info['team_name_cantonese']}")
        
        if debut_info['is_current']:
            print("  → Still represents this national team")
        else:
            print("  → Former national team")
    
    print(f"\n✓ All {len(questions)} questions saved to {output_file}")
    print("✓ Ready for Cantonese benchmark construction!")
