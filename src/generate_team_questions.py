#!/usr/bin/env python3
"""
Generate multiple-choice questions about football players and their club affiliations.

This script uses the extracted player-club data to create benchmark questions
for testing LLM understanding of Cantonese football terminology.
"""

import json
import random
from typing import List, Dict, Any, Tuple
from datetime import datetime


def load_player_data(file_path: str) -> Dict[str, Any]:
    """Load the complete player club data."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


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


def get_popular_clubs(all_data: Dict[str, Any], min_players: int = 3) -> List[Dict[str, Any]]:
    """Get clubs that have had multiple players (good for distractors)."""
    club_to_players = all_data.get('club_to_players_mapping', {})
    popular_clubs = []
    
    for club_id, players_list in club_to_players.items():
        if len(players_list) >= min_players:
            # Get club name from any player's data
            club_name = "Unknown Club"
            for player_data in all_data['players'].values():
                for club in player_data['clubs']:
                    if club['club_id'] == club_id:
                        club_name = club['name']
                        break
                if club_name != "Unknown Club":
                    break
            
            # Filter out national teams
            if any(keyword in club_name.lower() for keyword in ['national', 'under-', 'youth']):
                continue
                
            popular_clubs.append({
                'id': club_id,
                'name': club_name,
                'player_count': len(players_list)
            })
    
    return popular_clubs


def generate_team_question(player_id: str, player_data: Dict[str, Any], 
                          popular_clubs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate a multiple-choice question about which team a player has played for."""
    
    player_name = player_data.get('player_name', 'Unknown Player')
    player_clubs = get_football_clubs_only(player_data)
    
    if not player_clubs:
        return None
    
    # Choose a correct answer (one of the clubs the player actually played for)
    correct_club = random.choice(player_clubs)
    correct_answer = correct_club['name']
    
    # Generate 3 incorrect options from popular clubs
    player_club_ids = {club['club_id'] for club in player_clubs}
    available_distractors = [
        club for club in popular_clubs 
        if club['id'] not in player_club_ids and club['name'] != correct_answer
    ]
    
    if len(available_distractors) < 3:
        return None  # Not enough distractors available
    
    distractors = random.sample(available_distractors, 3)
    distractor_names = [club['name'] for club in distractors]
    
    # Create answer choices
    choices = [correct_answer] + distractor_names
    random.shuffle(choices)
    
    # Find the correct answer index
    correct_index = choices.index(correct_answer)
    correct_letter = ['A', 'B', 'C', 'D'][correct_index]
    
    question_data = {
        'question': f"Which team has {player_name} played for?",
        'choices': {
            'A': choices[0],
            'B': choices[1], 
            'C': choices[2],
            'D': choices[3]
        },
        'correct_answer': correct_letter,
        'correct_club_info': {
            'name': correct_answer,
            'id': correct_club['club_id'],
            'start_year': correct_club.get('start_year'),
            'end_year': correct_club.get('end_year'),
            'is_current': correct_club.get('is_current', False)
        },
        'player_info': {
            'name': player_name,
            'id': player_id,
            'total_clubs': len(player_clubs)
        },
        'distractors': distractor_names,
        'question_type': 'player_team_affiliation'
    }
    
    return question_data


def generate_multiple_questions(all_data: Dict[str, Any], 
                              num_questions: int = 50) -> List[Dict[str, Any]]:
    """Generate multiple team affiliation questions."""
    
    players = all_data.get('players', {})
    popular_clubs = get_popular_clubs(all_data, min_players=2)
    
    print(f"Found {len(popular_clubs)} popular clubs for distractors")
    
    questions = []
    attempts = 0
    max_attempts = num_questions * 5  # Prevent infinite loop
    
    # Get players with multiple football clubs (more interesting questions)
    eligible_players = []
    for player_id, player_data in players.items():
        football_clubs = get_football_clubs_only(player_data)
        if len(football_clubs) >= 1 and player_data.get('player_name'):
            eligible_players.append((player_id, player_data))
    
    print(f"Found {len(eligible_players)} eligible players")
    
    while len(questions) < num_questions and attempts < max_attempts:
        attempts += 1
        
        # Randomly select a player
        player_id, player_data = random.choice(eligible_players)
        
        # Generate question
        question = generate_team_question(player_id, player_data, popular_clubs)
        
        if question:
            # Avoid duplicate players (for variety)
            if not any(q['player_info']['id'] == player_id for q in questions):
                questions.append(question)
    
    return questions


def format_question_for_display(question_data: Dict[str, Any]) -> str:
    """Format a question for human-readable display."""
    
    formatted = f'"""\n{question_data["question"]}\n'
    for letter in ['A', 'B', 'C', 'D']:
        formatted += f'{letter}. {question_data["choices"][letter]}\n'
    formatted += '"""'
    
    return formatted


def save_questions(questions: List[Dict[str, Any]], output_file: str):
    """Save questions to a JSON file with metadata."""
    
    output_data = {
        'metadata': {
            'description': 'Multiple-choice questions about football player team affiliations',
            'purpose': 'Cantonese benchmark for testing LLM understanding of football terminology',
            'question_type': 'player_team_affiliation',
            'total_questions': len(questions),
            'generation_date': datetime.now().isoformat(),
            'format': 'Four choices (A, B, C, D) with one correct answer'
        },
        'questions': questions
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    # Load the player data
    data_file = "./data/intermediate/football_players_clubs_complete.json"
    
    print("Loading player data...")
    all_data = load_player_data(data_file)
    
    print(f"Loaded data for {len(all_data['players'])} players")
    
    # Generate questions
    print("Generating team affiliation questions...")
    questions = generate_multiple_questions(all_data, num_questions=50)
    
    print(f"Generated {len(questions)} questions")
    
    # Save to file
    output_file = "./data/output/team_affiliation_questions.json"
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
        print(f"Player: {question['player_info']['name']} ({question['player_info']['total_clubs']} clubs)")
        print(f"Correct Club: {question['correct_club_info']['name']}")
        if question['correct_club_info']['is_current']:
            print("  → Current club")
        else:
            start = question['correct_club_info']['start_year'] or "?"
            end = question['correct_club_info']['end_year'] or "?"
            print(f"  → Former club ({start}-{end})")
    
    print(f"\n✓ All {len(questions)} questions saved to {output_file}")
    print("✓ Ready for Cantonese benchmark construction!")
