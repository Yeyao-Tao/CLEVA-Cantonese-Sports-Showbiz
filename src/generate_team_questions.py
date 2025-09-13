#!/usr/bin/env python3
"""
Generate multiple-choice questions about football players and their club affiliations.

This script uses the extracted player-club data to create benchmark questions
for testing LLM understanding of Cantonese football terminology.
"""

import json
import random
import os
import sys
from typing import List, Dict, Any, Tuple
from datetime import datetime

# Add the current directory to Python path to import utils
sys.path.append(os.path.dirname(__file__))

from utils.file_utils import load_player_data
from utils.path_utils import get_soccer_intermediate_dir, get_soccer_output_dir


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


def get_football_clubs_only(player_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get only football clubs (excluding national teams) for a player."""
    clubs = []
    for club in player_data.get('clubs', []):
        description = club.get('description', '').lower()
        name = club.get('name', '').lower()
        
        # Skip national teams and youth teams
        if any(keyword in description for keyword in ['national', 'under-', 'youth']):
            continue
        if any(keyword in name for keyword in ['national', 'under-', 'u-', 'youth']):
            continue
        
        clubs.append(club)
    
    return clubs


def get_popular_national_teams(all_data: Dict[str, Any], min_players: int) -> List[Dict[str, Any]]:
    """Get national teams that have had multiple players (good for distractors)."""
    national_teams = all_data.get('all_national_teams', {})
    team_to_players = all_data.get('national_team_to_players_mapping', {})
    popular_teams = []
    
    for team_id, players_list in team_to_players.items():
        if len(players_list) >= min_players:
            team = national_teams[team_id]
            team_name = team['club_names']['english']

            # Filter out youth teams
            if any(keyword in team_name.lower() for keyword in ['under-', 'youth', 'u-']):
                continue

            # Filter for teams that have Cantonese names
            if team['has_cantonese']:
                popular_teams.append({
                    'id': team_id,
                    'name': team_name,
                    'name_cantonese': team['club_names']['cantonese_best'],
                    'player_count': len(players_list)
                })

    return popular_teams



def get_popular_clubs(all_data: Dict[str, Any], min_players: int) -> List[Dict[str, Any]]:
    """Get clubs that have had multiple players (good for distractors)."""
    clubs = all_data.get('all_clubs', {})
    club_to_players = all_data.get('club_to_players_mapping', {})
    popular_clubs = []
    
    for club_id, players_list in club_to_players.items():
        if len(players_list) >= min_players:
            club = clubs[club_id]
            club_name = club['club_names']['english']

            # Filter out national teams
            if any(keyword in club_name.lower() for keyword in ['national', 'under-', 'youth']):
                continue

            # Filter out clubs that have no Cantonese name
            if club['has_cantonese']:
                popular_clubs.append({
                    'id': club_id,
                    'name': club_name,
                    'name_cantonese': club['club_names']['cantonese_best'],
                    'player_count': len(players_list)
                })

    return popular_clubs


def calculate_club_tenure(club: Dict[str, Any]) -> int:
    """Calculate the tenure (in years) for a club. Returns 0 if dates are missing."""
    start_year = club.get('start_year')
    end_year = club.get('end_year')
    
    if start_year is None:
        return 0
    
    # If end_year is None, assume it's a current club and use current year (2025)
    if end_year is None:
        end_year = 2025
    
    # Ensure we don't have negative tenure
    return max(0, end_year - start_year)


def get_longest_tenure_club(player_clubs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Get the club where the player had the longest tenure."""
    if not player_clubs:
        return None
    
    # Calculate tenure for each club and find the one with maximum tenure
    club_with_max_tenure = max(player_clubs, key=calculate_club_tenure)
    return club_with_max_tenure


def generate_team_question(player_id: str, player_data: Dict[str, Any], 
                          popular_teams: List[Dict[str, Any]], all_data: Dict[str, Any],
                          team_type: str) -> Dict[str, Any]:
    """Generate a multiple-choice question about which team a player has played for."""
    
    # Get player names from player_names structure
    player_names = player_data.get('player_names', {})
    player_name = player_names.get('english', 'Unknown Player')
    cantonese_name = player_names.get('cantonese_best', player_name)
    
    if team_type == 'club':
        player_teams = get_football_clubs_only(player_data)
    elif team_type == 'national':
        player_teams = get_national_teams_only(player_data)
    else:
        return None

    if not player_teams:
        return None
    
    # Choose the team where the player had the longest tenure
    correct_team = get_longest_tenure_club(player_teams)
    if not correct_team:
        return None
        
    correct_answer = correct_team['name']
    correct_answer_cantonese = correct_team.get('cantonese_name', correct_answer)
    tenure_years = calculate_club_tenure(correct_team)
    
    # Generate 3 incorrect options from popular teams
    player_team_ids = {team['club_id'] for team in player_teams}
    available_distractors = [
        team for team in popular_teams 
        if team['id'] not in player_team_ids and team['name'] != correct_answer
    ]
    
    if len(available_distractors) < 3:
        return None  # Not enough distractors available
    
    distractors = random.sample(available_distractors, 3)
    distractor_names = [team['name'] for team in distractors]
    
    # Get Cantonese names for distractors (need to look them up from the data)
    distractor_names_cantonese = []
    for distractor in distractors:
        # Find the Cantonese name for this team from any player's data
        cantonese_distractor_name = distractor['name_cantonese']
        distractor_names_cantonese.append(cantonese_distractor_name)
    
    # Create answer choices - need to maintain same order for both languages
    all_choices = [correct_answer] + distractor_names
    all_choices_cantonese = [correct_answer_cantonese] + distractor_names_cantonese
    
    # Create a combined list to shuffle together
    combined_choices = list(zip(all_choices, all_choices_cantonese))
    random.shuffle(combined_choices)
    
    # Separate back into individual lists
    choices, choices_cantonese = zip(*combined_choices)
    choices = list(choices)
    choices_cantonese = list(choices_cantonese)
    
    # Find the correct answer indices
    correct_index = choices.index(correct_answer)
    correct_letter = ['A', 'B', 'C', 'D'][correct_index]
    
    question_text = f"Which team has {player_name} played for?"
    question_text_cantonese = f"{cantonese_name}曾經效力過邊隊？"
    if team_type == 'national':
        question_text = f"Which national team has {player_name} represented?"
        question_text_cantonese = f"{cantonese_name}曾經代表過邊隊國家隊？"

    question_data = {
        'question': question_text,
        'question_cantonese': question_text_cantonese,
        'choices': {
            'A': choices[0],
            'B': choices[1], 
            'C': choices[2],
            'D': choices[3]
        },
        'choices_cantonese': {
            'A': choices_cantonese[0],
            'B': choices_cantonese[1], 
            'C': choices_cantonese[2],
            'D': choices_cantonese[3]
        },
        'correct_answer': correct_letter,
        'correct_club_info': {
            'name': correct_answer,
            'name_cantonese': correct_answer_cantonese,
            'id': correct_team['club_id'],
            'start_year': correct_team.get('start_year'),
            'end_year': correct_team.get('end_year'),
            'tenure_years': tenure_years,
            'is_current': correct_team.get('is_current', False),
            'selection_reason': 'longest_tenure'
        },
        'player_info': {
            'name': player_name,
            'name_cantonese': cantonese_name,
            'id': player_id,
            'total_clubs': len(player_teams)
        },
        'distractors': distractor_names,
        'distractors_cantonese': distractor_names_cantonese,
        'question_type': f'player_{team_type}_affiliation'
    }
    
    return question_data


def generate_multiple_club_questions(all_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate multiple team affiliation questions for clubs."""
    
    players = all_data.get('players', {})
    popular_clubs = get_popular_clubs(all_data, min_players=5)
    
    print(f"Found {len(popular_clubs)} popular clubs for distractors")
    
    questions = []
    
    # Get players with multiple football clubs (more interesting questions)
    eligible_players = []
    for player_id, player_data in players.items():
        football_clubs = get_football_clubs_only(player_data)
        player_names = player_data.get('player_names', {})
        player_name = player_names.get('english')
        if len(football_clubs) >= 1 and player_name:
            eligible_players.append((player_id, player_data))
    
    print(f"Found {len(eligible_players)} eligible players for club questions")

    for player in eligible_players:
        player_id, player_data = player
        question = generate_team_question(player_id, player_data, popular_clubs, all_data, 'club')
        if question:
            questions.append(question)

    return questions


def generate_multiple_national_team_questions(all_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate multiple team affiliation questions for national teams."""
    
    players = all_data.get('players', {})
    popular_teams = get_popular_national_teams(all_data, min_players=2)
    
    print(f"Found {len(popular_teams)} popular national teams for distractors")
    
    questions = []
    
    # Get players with national team experience
    eligible_players = []
    for player_id, player_data in players.items():
        national_teams = get_national_teams_only(player_data)
        player_names = player_data.get('player_names', {})
        player_name = player_names.get('english')
        if len(national_teams) >= 1 and player_name:
            eligible_players.append((player_id, player_data))
            
    print(f"Found {len(eligible_players)} eligible players for national team questions")

    for player in eligible_players:
        player_id, player_data = player
        question = generate_team_question(player_id, player_data, popular_teams, all_data, 'national')
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
    
    output_data = {
        'metadata': {
            'description': 'Multiple-choice questions about football player team affiliations in English and Cantonese',
            'purpose': 'Cantonese benchmark for testing LLM understanding of football terminology',
            'question_type': 'player_team_affiliation',
            'languages': ['English', 'Cantonese'],
            'club_selection_method': 'longest_tenure',
            'total_questions': len(questions),
            'generation_date': datetime.now().isoformat(),
            'format': 'Four choices (A, B, C, D) with one correct answer in both languages'
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
    print("\nGenerating club affiliation questions...")
    club_questions = generate_multiple_club_questions(all_data)
    print(f"Generated {len(club_questions)} club questions")

    print("\nGenerating national team affiliation questions...")
    national_team_questions = generate_multiple_national_team_questions(all_data)
    print(f"Generated {len(national_team_questions)} national team questions")
    
    questions = club_questions + national_team_questions
    random.shuffle(questions)
    
    print(f"\nTotal questions generated: {len(questions)}")
    
    # Save to file
    output_file = os.path.join(get_soccer_output_dir(), "team_affiliation_questions.json")
    
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
        club_info = question['correct_club_info']
        team_type = 'club' if question['question_type'] == 'player_club_affiliation' else 'national team'
        
        print(f"Player: {player_info['name']} / {player_info['name_cantonese']} ({player_info['total_clubs']} {team_type}s)")
        print(f"Correct Club: {club_info['name']} / {club_info['name_cantonese']} ({club_info['tenure_years']} years)")
        if club_info['is_current']:
            print("  → Current team (longest tenure)")
        else:
            start = club_info['start_year'] or "?"
            end = club_info['end_year'] or "?"
            print(f"  → Former team ({start}-{end}, longest tenure)")
    
    print(f"\n✓ All {len(questions)} questions saved to {output_file}")
    print("✓ Ready for Cantonese benchmark construction!")
