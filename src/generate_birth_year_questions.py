#!/usr/bin/env python3
"""
Generate multiple-choice questions about football players' birth years.

This script uses the extracted player birth year data to create benchmark questions
for testing LLM understanding of Cantonese football terminology and player information.
"""

import json
import random
from typing import List, Dict, Any, Tuple
from datetime import datetime
import collections


def load_birth_year_data(file_path: str) -> Dict[str, Any]:
    """Load the complete player birth year data."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_birth_year_distribution(all_data: Dict[str, Any]) -> Dict[int, int]:
    """Get the distribution of birth years for generating distractors."""
    players = all_data.get('players', {})
    birth_years = []
    
    for player_data in players.values():
        birth_year = player_data.get('birth_year')
        if birth_year:
            birth_years.append(birth_year)
    
    return collections.Counter(birth_years)


def generate_birth_year_distractors(correct_year: int, year_distribution: Dict[int, int], num_distractors: int = 3) -> List[int]:
    """Generate plausible birth year distractors."""
    # Get all available years except the correct one
    available_years = [year for year in year_distribution.keys() if year != correct_year]
    
    if len(available_years) < num_distractors:
        # If we don't have enough actual years, generate some nearby years
        nearby_years = []
        for offset in [1, -1, 2, -2, 3, -3, 4, -4, 5, -5]:
            candidate = correct_year + offset
            if candidate not in [correct_year] + available_years and 1970 <= candidate <= 2010:
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


def generate_birth_year_question(player_id: str, player_data: Dict[str, Any], 
                                year_distribution: Dict[int, int]) -> Dict[str, Any]:
    """Generate a multiple-choice question about a player's birth year."""
    
    player_names = player_data.get('player_names', {})
    player_name = player_names.get('english', 'Unknown Player')
    cantonese_name = player_names.get('cantonese_best', player_name)
    birth_year = player_data.get('birth_year')
    birth_date = player_data.get('birth_date', '')
    
    if not birth_year:
        return None
    
    # Generate distractors
    distractors = generate_birth_year_distractors(birth_year, year_distribution)
    
    if len(distractors) < 3:
        return None  # Not enough distractors available
    
    # Create answer choices
    all_choices = [birth_year] + distractors
    random.shuffle(all_choices)
    
    # Find the correct answer index
    correct_index = all_choices.index(birth_year)
    correct_letter = ['A', 'B', 'C', 'D'][correct_index]
    
    question_data = {
        'question': f"What year was {player_name}, the soccer player, born?",
        'question_cantonese': f"足球員{cantonese_name}係邊年出世？",
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
        'correct_birth_info': {
            'birth_year': birth_year,
            'birth_date': birth_date,
            'age_in_2025': 2025 - birth_year
        },
        'player_info': {
            'name': player_name,
            'name_cantonese': cantonese_name,
            'id': player_id
        },
        'distractors': [str(d) for d in distractors],
        'question_type': 'player_birth_year'
    }
    
    return question_data


def generate_age_question(player_id: str, player_data: Dict[str, Any], 
                         year_distribution: Dict[int, int]) -> Dict[str, Any]:
    """Generate a multiple-choice question about a player's current age."""
    
    player_names = player_data.get('player_names', {})
    player_name = player_names.get('english', 'Unknown Player')
    cantonese_name = player_names.get('cantonese_best', player_name)
    birth_year = player_data.get('birth_year')
    
    if not birth_year:
        return None
    
    current_age = 2025 - birth_year
    
    # Generate age distractors (±1 to ±3 years)
    age_distractors = []
    for offset in [1, -1, 2, -2, 3, -3]:
        candidate_age = current_age + offset
        if candidate_age > 0 and candidate_age not in age_distractors:
            age_distractors.append(candidate_age)
    
    if len(age_distractors) < 3:
        return None
    
    distractors = age_distractors[:3]
    
    # Create answer choices
    all_choices = [current_age] + distractors
    random.shuffle(all_choices)
    
    # Find the correct answer index
    correct_index = all_choices.index(current_age)
    correct_letter = ['A', 'B', 'C', 'D'][correct_index]
    
    question_data = {
        'question': f"How old is {player_name}, the soccer player, in 2025?",
        'question_cantonese': f"足球員{cantonese_name}喺2025年幾多歲？",
        'choices': {
            'A': str(all_choices[0]),
            'B': str(all_choices[1]), 
            'C': str(all_choices[2]),
            'D': str(all_choices[3])
        },
        'choices_cantonese': {
            'A': f"{all_choices[0]}歲",
            'B': f"{all_choices[1]}歲", 
            'C': f"{all_choices[2]}歲",
            'D': f"{all_choices[3]}歲"
        },
        'correct_answer': correct_letter,
        'correct_birth_info': {
            'birth_year': birth_year,
            'birth_date': player_data.get('birth_date', ''),
            'age_in_2025': current_age
        },
        'player_info': {
            'name': player_name,
            'name_cantonese': cantonese_name,
            'id': player_id
        },
        'distractors': [str(d) for d in distractors],
        'question_type': 'player_current_age'
    }
    
    return question_data


def generate_youngest_oldest_question(all_data: Dict[str, Any], question_type: str) -> Dict[str, Any]:
    """Generate questions about the youngest or oldest player among a random sample."""
    
    players = all_data.get('players', {})
    players_with_dates = []
    
    for player_id, player_data in players.items():
        birth_date = player_data.get('birth_date')
        birth_year = player_data.get('birth_year')
        if birth_date or birth_year:  # Accept players with either birth_date or birth_year
            players_with_dates.append((player_id, player_data))
    
    if len(players_with_dates) < 4:
        return None
    
    # Randomly sample 4 players from all available players
    sampled_players = random.sample(players_with_dates, 4)
    
    # Sort the sampled players by birth date (or birth year as fallback) to find youngest/oldest among them
    def get_birth_sort_key(player_tuple):
        player_id, player_data = player_tuple
        birth_date = player_data.get('birth_date')
        if birth_date:
            # Parse birth_date string like "1994-05-27T00:00:00Z" to datetime for accurate sorting
            try:
                # Handle timezone-aware and timezone-naive datetime strings
                if birth_date.endswith('Z'):
                    return datetime.fromisoformat(birth_date.replace('Z', '+00:00')).replace(tzinfo=None)
                else:
                    return datetime.fromisoformat(birth_date).replace(tzinfo=None)
            except (ValueError, AttributeError):
                # Fallback to birth_year if birth_date parsing fails
                birth_year = player_data.get('birth_year')
                if birth_year:
                    return datetime(birth_year, 1, 1)  # Use January 1st as default
                return datetime(1900, 1, 1)  # Default very old date
        else:
            # Fallback to birth_year
            birth_year = player_data.get('birth_year')
            if birth_year:
                return datetime(birth_year, 1, 1)  # Use January 1st as default
            return datetime(1900, 1, 1)  # Default very old date
    
    if question_type == 'youngest':
        sampled_players.sort(key=get_birth_sort_key, reverse=True)  # Most recent birth date
        question_text = "Who is the youngest player among these options?"
        question_cantonese = "邊個係呢啲選擇入面最後生嘅球員？"
    else:  # oldest
        sampled_players.sort(key=get_birth_sort_key)  # Earliest birth date
        question_text = "Who is the oldest player among these options?"
        question_cantonese = "邊個係呢啲選擇入面最年長嘅球員？"
    
    # Get the correct answer (youngest/oldest among the 4 sampled players)
    correct_player_id, correct_player_data = sampled_players[0]
    correct_player_names = correct_player_data.get('player_names', {})
    correct_name = correct_player_names.get('english', 'Unknown Player')
    correct_cantonese_name = correct_player_names.get('cantonese_best', correct_name)
    correct_birth_year = correct_player_data.get('birth_year')
    
    # Get distractors from the other 3 sampled players
    distractors = []
    for player_id, player_data in sampled_players[1:]:
        player_names = player_data.get('player_names', {})
        name = player_names.get('english', 'Unknown Player')
        cantonese_name = player_names.get('cantonese_best', name)
        birth_year = player_data.get('birth_year')
        distractors.append((name, cantonese_name, birth_year))
    
    # Create answer choices from all 4 sampled players
    all_choices = [(correct_name, correct_cantonese_name, correct_birth_year)] + distractors
    random.shuffle(all_choices)
    
    # Find the correct answer index
    correct_index = next(i for i, (name, _, _) in enumerate(all_choices) if name == correct_name)
    correct_letter = ['A', 'B', 'C', 'D'][correct_index]
    
    question_data = {
        'question': question_text,
        'question_cantonese': question_cantonese,
        'choices': {
            'A': all_choices[0][0],
            'B': all_choices[1][0], 
            'C': all_choices[2][0],
            'D': all_choices[3][0]
        },
        'choices_cantonese': {
            'A': all_choices[0][1],
            'B': all_choices[1][1], 
            'C': all_choices[2][1],
            'D': all_choices[3][1]
        },
        'correct_answer': correct_letter,
        'correct_birth_info': {
            'birth_year': correct_birth_year,
            'birth_date': correct_player_data.get('birth_date', ''),
            'age_in_2025': 2025 - correct_birth_year if correct_birth_year else None
        },
        'player_info': {
            'name': correct_name,
            'name_cantonese': correct_cantonese_name,
            'id': correct_player_id
        },
        'distractors': [name for name, _, _ in all_choices if name != correct_name],
        'distractors_cantonese': [cantonese_name for name, cantonese_name, _ in all_choices if name != correct_name],
        'question_type': f'player_{question_type}'
    }
    
    return question_data


def generate_multiple_questions(all_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate multiple birth year related questions."""
    
    players = all_data.get('players', {})
    year_distribution = get_birth_year_distribution(all_data)
    
    print(f"Found {len(players)} players with birth year data")
    print(f"Birth year range: {min(year_distribution.keys())} - {max(year_distribution.keys())}")
    
    questions = []
    
    # Generate birth year questions
    print("Generating birth year questions...")
    player_list = list(players.items())
    random.shuffle(player_list)
    
    birth_year_questions = 0
    age_questions = 0
    
    for player_id, player_data in player_list:
        question = generate_birth_year_question(player_id, player_data, year_distribution)
        if question:
            questions.append(question)
            birth_year_questions += 1
        
        question = generate_age_question(player_id, player_data, year_distribution)
        if question:
            questions.append(question)
            age_questions += 1
    
    # Generate youngest/oldest questions
    print("Generating youngest/oldest player questions...")
    for question_type in ['youngest', 'oldest']:
        for _ in range(100):  # Generate a few of these
            question = generate_youngest_oldest_question(all_data, question_type)
            if question:
                questions.append(question)
    
    print(f"Generated {len(questions)} total questions")
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
    
    question_types = {}
    for question in questions:
        q_type = question['question_type']
        question_types[q_type] = question_types.get(q_type, 0) + 1
    
    output_data = {
        'metadata': {
            'description': 'Multiple-choice questions about football player birth years and ages in English and Cantonese',
            'purpose': 'Cantonese benchmark for testing LLM understanding of player biographical information',
            'question_types': list(question_types.keys()),
            'question_type_distribution': question_types,
            'languages': ['English', 'Cantonese'],
            'total_questions': len(questions),
            'generation_date': datetime.now().isoformat(),
            'format': 'Four choices (A, B, C, D) with one correct answer in both languages'
        },
        'questions': questions
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    # Load the birth year data
    data_file = "./data/intermediate/players_birth_years.json"
    
    print("Loading player birth year data...")
    all_data = load_birth_year_data(data_file)
    
    print(f"Loaded data for {len(all_data['players'])} players")
    
    # Generate questions
    print("Generating birth year and age questions...")
    questions = generate_multiple_questions(all_data)
    
    print(f"Generated {len(questions)} questions")
    
    # Save to file
    output_file = "./data/output/birth_year_questions.json"
    save_questions(questions, output_file)
    
    print(f"Questions saved to {output_file}")
    
    # Display 5 questions for each type as examples
    print("\n" + "="*80)
    print("SAMPLE QUESTIONS (5 per type)")
    print("="*80)
    
    # Group questions by type
    questions_by_type = {}
    for question in questions:
        q_type = question['question_type']
        if q_type not in questions_by_type:
            questions_by_type[q_type] = []
        questions_by_type[q_type].append(question)
    
    # Display 5 questions for each type
    question_counter = 1
    for q_type in ['player_birth_year', 'player_current_age', 'player_youngest', 'player_oldest']:
        if q_type in questions_by_type:
            print(f"\n{'-'*40}")
            print(f"{q_type.replace('_', ' ').title()} Questions:")
            print(f"{'-'*40}")
            
            for i, question in enumerate(questions_by_type[q_type][:5], 1):
                print(f"\nQuestion {question_counter} ({question['question_type']}):")
                print(format_question_for_display(question))
                print(f"Correct Answer: {question['correct_answer']}")
                
                if 'player_info' in question:
                    print(f"Player: {question['player_info']['name']} / {question['player_info']['name_cantonese']}")
                
                if 'correct_birth_info' in question:
                    birth_info = question['correct_birth_info']
                    print(f"Birth Year: {birth_info.get('birth_year', 'N/A')}, Age in 2025: {birth_info.get('age_in_2025', 'N/A')}")
                
                question_counter += 1
    
    print(f"\n✓ All {len(questions)} questions saved to {output_file}")
    print("✓ Ready for Cantonese benchmark construction!")
