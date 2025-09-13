# National Team Debut Year Questions Generator

This script generates multiple-choice questions in Cantonese about when football players first debuted for their senior national teams.

## Overview

The `generate_debut_year_questions.py` script creates benchmark questions for testing LLM understanding of Cantonese football terminology, specifically focusing on player career timelines and national team debuts.

## Features

- **Smart Youth Team Filtering**: Automatically excludes youth/under-age teams (U-21, U-19, etc.) to focus only on senior national team debuts
- **Realistic Distractors**: Generates distractor years based on the actual distribution of debut years in the dataset
- **Bilingual Questions**: Creates questions in both English and Cantonese with appropriate formatting
- **Comprehensive Metadata**: Includes detailed information about players, teams, and debut circumstances

## Usage

```bash
python src/generate_debut_year_questions.py
```

The script will:
1. Load player data from `data/soccer/intermediate/football_players_clubs_complete.json`
2. Analyze debut year distribution across all players
3. Generate questions for players with known national team debut years
4. Save results to `data/soccer/output/debut_year_questions.json`

## Question Format

Each question asks when a player first debuted for their senior national team:

**English**: "In which year did [Player Name] first debut for the senior national team?"
**Cantonese**: "[Player Cantonese Name]喺邊一年首次代表成年國家隊出賽？"

**Answer Choices**: Four years (A, B, C, D) with one correct answer
**Cantonese Choices**: Include "年" suffix (e.g., "2010年")

## Example Output

```json
{
  "question": "In which year did Lionel Messi first debut for the senior national team?",
  "question_cantonese": "美斯喺邊一年首次代表成年國家隊出賽？",
  "choices": {
    "A": "2011",
    "B": "2005", 
    "C": "2015",
    "D": "2004"
  },
  "choices_cantonese": {
    "A": "2011年",
    "B": "2005年",
    "C": "2015年", 
    "D": "2004年"
  },
  "correct_answer": "B",
  "debut_info": {
    "year": 2005,
    "team_name": "Argentina men's national association football team",
    "team_name_cantonese": "阿根廷足球代表隊",
    "is_current": true
  }
}
```

## Algorithm Details

### Youth Team Filtering
The script identifies and excludes youth teams by checking for keywords:
- "under-", "youth", "u-" in team names or descriptions
- Examples filtered out: "Spain U-21", "France youth team"

### Debut Year Selection
For players with multiple national teams:
- Only considers senior national teams
- Selects the earliest debut year among all senior teams
- Requires valid `start_year` data

### Distractor Generation
Creates realistic distractor years by:
- Analyzing the distribution of actual debut years in the dataset
- Preferring more common years as distractors
- Generating nearby years if insufficient real data
- Ensuring no duplicate of the correct year

## Data Requirements

The script expects player data with the following structure:
```json
{
  "national_teams": [
    {
      "start_year": 2010,
      "name": "Spain men's national football team",
      "cantonese_name": "西班牙足球代表隊",
      "description": "men's national association football team representing Spain",
      "is_current": false
    }
  ]
}
```

## Statistics

When run on the current dataset:
- **Total Questions**: 139
- **Year Range**: 1997-2021
- **Current Teams**: 60 players still represent their debut team
- **Former Teams**: 79 players no longer represent their debut team

## Testing

Run the unit tests to verify functionality:
```bash
python -m pytest tests/unit/test_debut_year_questions.py -v
```

The tests cover:
- Youth team filtering
- Earliest debut detection
- Distractor generation
- Complete question generation
- Edge cases (no teams, missing data)

## Related Scripts

- `generate_team_questions.py`: Generates questions about which teams players have represented
- `generate_birth_year_questions.py`: Generates questions about player birth years
- `generate_teammate_questions.py`: Generates questions about teammate relationships

## Output File

The generated questions are saved to `data/soccer/output/debut_year_questions.json` with comprehensive metadata including:
- Question type and purpose
- Total number of questions
- Year range covered
- Current vs. former team distribution
- Generation timestamp
