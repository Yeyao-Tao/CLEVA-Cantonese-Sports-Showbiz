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
    input_file = "./data/intermediate/football_players_clubs_complete.json"
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        return False
    
    # Load the data
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✓ Successfully loaded data with {len(data.get('players', {}))} players")
    except Exception as e:
        print(f"❌ Failed to load data: {e}")
        return False
    
    # Check if potential_teammates exists
    if 'potential_teammates' not in data:
        print("❌ No 'potential_teammates' field found in data")
        return False
    
    potential_teammates = data['potential_teammates']
    print(f"✓ Found {len(potential_teammates)} potential teammate pairs")
    
    # Check the structure of the first teammate pair
    if potential_teammates:
        first_pair = potential_teammates[0]
        required_fields = ['player1', 'player2', 'club']
        for field in required_fields:
            if field not in first_pair:
                print(f"❌ Missing field '{field}' in teammate pair")
                return False
        
        # Check player structure
        for player_key in ['player1', 'player2']:
            player = first_pair[player_key]
            player_fields = ['id', 'name_english', 'name_cantonese', 'has_cantonese']
            for field in player_fields:
                if field not in player:
                    print(f"❌ Missing field '{field}' in {player_key}")
                    return False
        
        print("✓ Teammate pair structure is valid")
    
    # Check if output file was generated
    output_file = "./data/output/teammate_relationship_questions.json"
    if not os.path.exists(output_file):
        print(f"❌ Output file not found: {output_file}")
        return False
    
    # Verify output file structure
    try:
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
                if field not in first_question:
                    print(f"❌ Missing field '{field}' in question")
                    return False
            print("✓ Question structure is valid")
        
    except Exception as e:
        print(f"❌ Failed to verify output file: {e}")
        return False
    
    print("✅ All tests passed!")
    return True

if __name__ == "__main__":
    success = test_teammate_questions()
    if not success:
        sys.exit(1)
