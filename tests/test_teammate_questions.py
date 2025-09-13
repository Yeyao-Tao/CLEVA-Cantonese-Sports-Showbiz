#!/usr/bin/env python3
"""
Simple test script to verify the teammate questions generation works correctly.
"""

import json
import sys
import os

# Add the src directory to the path so we can import our script
sys.path.append('./src')

def test_teammate_questions():
    """Test the teammate questions generation functionality."""
    
    print("Testing teammate questions generation...")
    
    # Check if the input file exists
    input_file = "./data/soccer/intermediate/football_players_clubs_complete.json"
    assert os.path.exists(input_file), f"Input file not found: {input_file}"
    
    # Load the data
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"✓ Successfully loaded data with {len(data.get('players', {}))} players")
    
    # Check if club_teammates exists
    assert 'club_teammates' in data, "No 'club_teammates' field found in data"
    
    club_teammates = data['club_teammates']
    print(f"✓ Found {len(club_teammates)} potential club teammate pairs")
    
    # Check the structure of the first teammate pair
    if club_teammates:
        first_pair = club_teammates[0]
        required_fields = ['player1', 'player2', 'team']
        for field in required_fields:
            assert field in first_pair, f"Missing field '{field}' in teammate pair"
        
        # Check player structure
        for player_key in ['player1', 'player2']:
            player = first_pair[player_key]
            player_fields = ['id', 'name_english', 'name_cantonese', 'has_cantonese']
            for field in player_fields:
                assert field in player, f"Missing field '{field}' in {player_key}"
        
        print("✓ Teammate pair structure is valid")
    
    # Check if output file was generated
    output_file = "./data/soccer/output/teammate_relationship_questions.json"
    assert os.path.exists(output_file), f"Output file not found: {output_file}"
    
    # Verify output file structure
    with open(output_file, 'r', encoding='utf-8') as f:
        output_data = json.load(f)
        
        if 'metadata' not in output_data or 'questions' not in output_data:
            print("❌ Invalid output file structure")
            return False
        
        questions = output_data['questions']
        print(f"✓ Generated {len(questions)} teammate questions")
        
        # Check the structure of the first question
        if questions:
            first_question = questions[0]
            required_question_fields = [
                'question', 'question_cantonese', 'choices', 'choices_cantonese',
                'correct_answer', 'correct_pair_info', 'explanations', 'explanations_cantonese'
            ]
            for field in required_question_fields:
                assert field in first_question, f"Missing field '{field}' in question"
            print("✓ Question structure is valid")
    
    print("✅ All tests passed!")

if __name__ == "__main__":
    test_teammate_questions()
