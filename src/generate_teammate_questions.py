#!/usr/bin/env python3
"""
Generate multiple-choice questions about whether two football players have been club teammates.

This script uses the extracted player-club data to create benchmark questions
for testing LLM understanding of Cantonese football terminology and club player relationships.
Note: This focuses specifically on club teammates, not national team teammates.
"""

import json
import random
from typing import List, Dict, Any, Tuple
from datetime import datetime


def load_player_data(file_path: str) -> Dict[str, Any]:
    """Load the complete player club data."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_player_names(player_id: str, all_data: Dict[str, Any]) -> Tuple[str, str]:
    """Get English and Cantonese names for a player."""
    players = all_data.get('players', {})
    if player_id not in players:
        return None, None
    
    player_data = players[player_id]
    player_names = player_data.get('player_names', {})
    english_name = player_names.get('english', 'Unknown Player')
    cantonese_name = player_names.get('cantonese_best', english_name)
    
    return english_name, cantonese_name


def get_random_non_teammates(all_data: Dict[str, Any], 
                            exclude_pairs: set, 
                            num_pairs: int = 3) -> List[Tuple[str, str]]:
    """Get random pairs of players who were NOT teammates."""
    players = all_data.get('players', {})
    player_ids = list(players.keys())
    
    non_teammate_pairs = []
    attempts = 0
    max_attempts = 1000  # Prevent infinite loop
    
    while len(non_teammate_pairs) < num_pairs and attempts < max_attempts:
        # Pick two random players
        player1_id = random.choice(player_ids)
        player2_id = random.choice(player_ids)
        
        if player1_id == player2_id:
            attempts += 1
            continue
        
        # Create a normalized pair (smaller ID first)
        pair = tuple(sorted([player1_id, player2_id]))
        
        # Check if this pair was teammates (in exclude_pairs)
        if pair not in exclude_pairs and pair not in [tuple(sorted([p1, p2])) for p1, p2 in non_teammate_pairs]:
            # Verify both players have valid names
            name1_en, name1_zh = get_player_names(player1_id, all_data)
            name2_en, name2_zh = get_player_names(player2_id, all_data)
            
            if name1_en and name2_en and name1_zh and name2_zh:
                non_teammate_pairs.append((player1_id, player2_id))
        
        attempts += 1
    
    return non_teammate_pairs


def generate_teammate_question(teammate_pair: Dict[str, Any], 
                             all_data: Dict[str, Any],
                             all_teammate_pairs: set) -> Dict[str, Any]:
    """Generate a multiple-choice question about which pair of players has been club teammates."""
    
    # Extract player information
    player1_data = teammate_pair['player1']
    player2_data = teammate_pair['player2']
    team_data = teammate_pair['team']  # Updated to use 'team' instead of 'club'
    
    player1_id = player1_data['id']
    player2_id = player2_data['id']
    
    player1_name_en = player1_data['name_english']
    player1_name_zh = player1_data['name_cantonese']
    player2_name_en = player2_data['name_english']
    player2_name_zh = player2_data['name_cantonese']
    
    team_name_en = team_data['name_english']
    team_name_zh = team_data['name_cantonese']
    
    # Generate 3 distractor pairs (players who were NOT teammates)
    distractor_pairs = get_random_non_teammates(all_data, all_teammate_pairs, 3)
    
    if len(distractor_pairs) < 3:
        return None  # Not enough distractors
    
    # Format the question choices
    choices_data = []
    
    # Add the correct answer (actual teammates)
    choices_data.append({
        'text_en': f"{player1_name_en} and {player2_name_en}",
        'text_zh': f"{player1_name_zh}同{player2_name_zh}",
        'is_correct': True,
        'explanation_en': f"They were teammates at {team_name_en}",
        'explanation_zh': f"佢哋喺{team_name_zh}做過隊友"
    })
    
    # Add distractor answers (non-teammates)
    for i, (dist_p1_id, dist_p2_id) in enumerate(distractor_pairs):
        dist_p1_name_en, dist_p1_name_zh = get_player_names(dist_p1_id, all_data)
        dist_p2_name_en, dist_p2_name_zh = get_player_names(dist_p2_id, all_data)
        
        choices_data.append({
            'text_en': f"{dist_p1_name_en} and {dist_p2_name_en}",
            'text_zh': f"{dist_p1_name_zh}同{dist_p2_name_zh}",
            'is_correct': False,
            'explanation_en': f"They have never been teammates",
            'explanation_zh': f"佢哋從來冇做過隊友"
        })
    
    # Shuffle the choices
    random.shuffle(choices_data)
    
    # Find the correct answer index
    correct_index = next(i for i, choice in enumerate(choices_data) if choice['is_correct'])
    correct_letter = ['A', 'B', 'C', 'D'][correct_index]
    
    # Create the question
    question_data = {
        'question': "Which two players below have been teammates in the same club before?",
        'question_cantonese': "以下邊對球員曾經喺同一間球會做過隊友？",
        'choices': {
            'A': choices_data[0]['text_en'],
            'B': choices_data[1]['text_en'],
            'C': choices_data[2]['text_en'],
            'D': choices_data[3]['text_en']
        },
        'choices_cantonese': {
            'A': choices_data[0]['text_zh'],
            'B': choices_data[1]['text_zh'],
            'C': choices_data[2]['text_zh'],
            'D': choices_data[3]['text_zh']
        },
        'correct_answer': correct_letter,
        'correct_pair_info': {
            'player1': {
                'id': player1_id,
                'name_english': player1_name_en,
                'name_cantonese': player1_name_zh,
                'start_year': player1_data.get('start_year'),
                'end_year': player1_data.get('end_year')
            },
            'player2': {
                'id': player2_id,
                'name_english': player2_name_en,
                'name_cantonese': player2_name_zh,
                'start_year': player2_data.get('start_year'),
                'end_year': player2_data.get('end_year')
            },
            'club': {
                'id': team_data['id'],
                'name_english': team_name_en,
                'name_cantonese': team_name_zh,
                'type': team_data.get('type', 'club')  # Include team type information
            }
        },
        'explanations': {
            'A': choices_data[0]['explanation_en'],
            'B': choices_data[1]['explanation_en'],
            'C': choices_data[2]['explanation_en'],
            'D': choices_data[3]['explanation_en']
        },
        'explanations_cantonese': {
            'A': choices_data[0]['explanation_zh'],
            'B': choices_data[1]['explanation_zh'],
            'C': choices_data[2]['explanation_zh'],
            'D': choices_data[3]['explanation_zh']
        },
        'question_type': 'teammate_relationship'
    }
    
    return question_data


def generate_multiple_teammate_questions(all_data: Dict[str, Any], 
                                       num_questions: int = 50) -> List[Dict[str, Any]]:
    """Generate multiple club teammate relationship questions."""
    
    # Use the new schema with separate club_teammates and national_teammates
    club_teammates = all_data.get('club_teammates', [])
    
    print(f"Found {len(club_teammates)} potential club teammate pairs")
    
    # Create a set of all teammate pairs for generating distractors
    teammate_pairs_set = set()
    for pair in club_teammates:
        player1_id = pair['player1']['id']
        player2_id = pair['player2']['id']
        normalized_pair = tuple(sorted([player1_id, player2_id]))
        teammate_pairs_set.add(normalized_pair)
    
    # Filter pairs that have Cantonese names for both players and the club
    valid_pairs = []
    for pair in club_teammates:
        if (pair['player1'].get('has_cantonese', False) and 
            pair['player2'].get('has_cantonese', False) and
            pair['team'].get('has_cantonese', False)):  # Updated to use 'team' instead of 'club'
            valid_pairs.append(pair)
    
    print(f"Found {len(valid_pairs)} valid pairs with Cantonese names")
    
    if len(valid_pairs) < num_questions:
        print(f"Only {len(valid_pairs)} valid pairs available, generating all of them")
        num_questions = len(valid_pairs)
    
    # Sample the pairs to use for questions
    selected_pairs = random.sample(valid_pairs, num_questions)
    
    questions = []
    for i, pair in enumerate(selected_pairs, 1):
        print(f"Generating question {i}/{num_questions}...")
        question = generate_teammate_question(pair, all_data, teammate_pairs_set)
        if question:
            questions.append(question)
    
    return questions


def format_teammate_question_for_display(question_data: Dict[str, Any]) -> str:
    """Format a teammate question for human-readable display."""
    
    formatted = f'"""\nEnglish: {question_data["question"]}\n'
    for letter in ['A', 'B', 'C', 'D']:
        formatted += f'{letter}. {question_data["choices"][letter]}\n'
    
    formatted += f'\nCantonese: {question_data["question_cantonese"]}\n'
    for letter in ['A', 'B', 'C', 'D']:
        formatted += f'{letter}. {question_data["choices_cantonese"][letter]}\n'
    formatted += '"""'
    
    return formatted


def save_teammate_questions(questions: List[Dict[str, Any]], output_file: str):
    """Save teammate questions to a JSON file with metadata."""
    
    output_data = {
        'metadata': {
            'description': 'Multiple-choice questions about football player club teammate relationships in English and Cantonese',
            'purpose': 'Cantonese benchmark for testing LLM understanding of football club player relationships',
            'question_type': 'club_teammate_relationship',
            'languages': ['English', 'Cantonese'],
            'answer_format': 'Player pairs (e.g., "Player A and Player B")',
            'total_questions': len(questions),
            'generation_date': datetime.now().isoformat(),
            'format': 'Four choices (A, B, C, D) with one correct answer (actual club teammates) and three distractors (non-teammates)',
            'note': 'Focuses specifically on club teammates, not national team teammates'
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
    print(f"Found {len(all_data.get('club_teammates', []))} potential club teammate pairs")
    print(f"Found {len(all_data.get('national_teammates', []))} potential national teammate pairs")
    
    # Generate questions
    print("Generating club teammate relationship questions...")
    questions = generate_multiple_teammate_questions(all_data, num_questions=50)
    
    print(f"Generated {len(questions)} questions")
    
    # Save to file
    output_file = "./data/output/teammate_relationship_questions.json"
    save_teammate_questions(questions, output_file)
    
    print(f"Questions saved to {output_file}")
    
    # Display first 5 questions as examples
    print("\n" + "="*80)
    print("SAMPLE CLUB TEAMMATE RELATIONSHIP QUESTIONS")
    print("="*80)
    
    for i, question in enumerate(questions[:5], 1):
        print(f"\nQuestion {i}:")
        print(format_teammate_question_for_display(question))
        print(f"Correct Answer: {question['correct_answer']}")
        
        correct_info = question['correct_pair_info']
        club_info = correct_info['club']
        player1_info = correct_info['player1']
        player2_info = correct_info['player2']
        
        print(f"Teammates: {player1_info['name_english']} / {player1_info['name_cantonese']} & {player2_info['name_english']} / {player2_info['name_cantonese']}")
        print(f"Club: {club_info['name_english']} / {club_info['name_cantonese']}")
        print(f"Years: {player1_info['start_year']}-{player1_info['end_year']} & {player2_info['start_year']}-{player2_info['end_year']}")
        print(f"Explanation: {question['explanations'][question['correct_answer']]}")
    
    print(f"\n✓ All {len(questions)} club teammate questions saved to {output_file}")
    print("✓ Ready for Cantonese benchmark construction!")
