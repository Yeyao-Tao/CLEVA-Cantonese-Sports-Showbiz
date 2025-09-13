# Teammate Relationship Questions Generator

## Overview

The `src/generate_teammate_questions.py` script generates multiple-choice questions about whether two football players have been teammates. This complements the existing `src/generate_team_questions.py` script by focusing on player relationships rather than individual player-team affiliations.

## How It Works

### Data Source
The script reads from `./data/soccer/intermediate/football_players_clubs_complete.json`, specifically using the `potential_teammates` array that contains pairs of players who have played together at the same club.

### Question Format
Each question asks which pair of players has been teammates before, with four multiple-choice answers:
- **One correct answer**: A pair of players who were actually teammates
- **Three distractors**: Pairs of players who were never teammates

### Example Question
```
English: Which pair of players below has been teammates before?
A. Lionel Messi and Dani Carvajal
B. Neymar and Joshua Kimmich
C. João Cancelo and Nemanja Matić
D. Diego Costa and Joshua Kimmich

Cantonese: 以下邊對球員曾經做過隊友？
A. 美斯同丹尼卡華積
B. 尼馬同約素亞·劍米克
C. 簡些路同尼馬查馬迪
D. 迪亞高哥斯達同約素亞·劍米克
```

## Usage

### Basic Usage
```bash
python src/generate_teammate_questions.py
```

### What It Does
1. **Loads data** from `./data/soccer/intermediate/football_players_clubs_complete.json`
2. **Filters** for player pairs where both players have Cantonese names
3. **Generates** 50 multiple-choice questions (or fewer if insufficient data)
4. **Creates distractors** by selecting random pairs of players who were never teammates
5. **Saves** results to `./data/soccer/output/teammate_relationship_questions.json`

### Output Structure
The generated JSON file contains:
- **Metadata**: Description, question type, generation date, etc.
- **Questions array**: Each question includes:
  - English and Cantonese questions
  - Multiple choice answers in both languages
  - Correct answer identifier (A, B, C, or D)
  - Detailed information about the correct teammate pair
  - Explanations for all answers

## Key Features

### Bilingual Support
- Questions and answers in both English and Cantonese
- Uses authentic Cantonese player and club names from WikiData

### Quality Control
- Only includes players with verified Cantonese names
- Filters out national teams and youth teams for cleaner questions
- Validates that distractor pairs are truly non-teammates

### Rich Metadata
Each question includes detailed information about:
- Player IDs, names (English and Cantonese)
- Club information where they were teammates
- Time periods of their club memberships
- Explanations for why answers are correct or incorrect

## Testing

Run the test suite to verify functionality:
```bash
python tests/test_teammate_questions.py
```

## File Locations

- **Script**: `src/generate_teammate_questions.py`
- **Input**: `./data/soccer/intermediate/football_players_clubs_complete.json`
- **Output**: `./data/soccer/output/teammate_relationship_questions.json`
- **Tests**: `tests/test_teammate_questions.py`

## Integration with Existing Work

This script complements the existing `src/generate_team_questions.py` by providing a different type of football knowledge question:

- **Team affiliation questions**: "Which team has [player] played for?"
- **Teammate questions**: "Which pair of players below has been teammates before?"

Both question types use the same underlying data and follow similar bilingual formatting standards for consistency in the Cantonese football benchmark.
