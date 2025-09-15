#!/usr/bin/env python3
"""
Unit tests for the debut year questions generation script.
"""

import pytest
import json
import sys
import os

# Add the src directory to the path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from cleva.cantonese.soccer.generate_debut_year_questions import (
    get_national_teams_only,
    get_earliest_national_team_debut,
    get_debut_years_distribution,
    generate_realistic_distractor_years,
    generate_debut_year_question
)


class TestDebutYearQuestions:
    
    def setup_method(self):
        """Set up test data."""
        self.sample_player_data = {
            "player_names": {
                "english": "Test Player",
                "cantonese_best": "測試球員"
            },
            "national_teams": [
                {
                    "club_id": "Q42267",
                    "start_year": 2010,
                    "name": "Spain men's national football team",
                    "cantonese_name": "西班牙足球代表隊",
                    "description": "men's national association football team representing Spain",
                    "is_current": False
                },
                {
                    "club_id": "Q123456",
                    "start_year": 2008,
                    "name": "Spain U-21 national football team",
                    "cantonese_name": "西班牙U21足球代表隊",
                    "description": "under-21 national association football team representing Spain",
                    "is_current": False
                }
            ]
        }
        
        self.sample_all_data = {
            "players": {
                "Q1": {
                    "player_names": {"english": "Player 1", "cantonese_best": "球員一"},
                    "national_teams": [{"start_year": 2010}]
                },
                "Q2": {
                    "player_names": {"english": "Player 2", "cantonese_best": "球員二"},
                    "national_teams": [{"start_year": 2008}]
                },
                "Q3": {
                    "player_names": {"english": "Player 3", "cantonese_best": "球員三"},
                    "national_teams": [{"start_year": 2010}]
                }
            }
        }

    def test_get_national_teams_only(self):
        """Test filtering out youth teams."""
        result = get_national_teams_only(self.sample_player_data)
        
        # Should only return senior national team (exclude U-21)
        assert len(result) == 1
        assert result[0]["name"] == "Spain men's national football team"
        assert "U-21" not in result[0]["name"]

    def test_get_earliest_national_team_debut(self):
        """Test getting the earliest debut."""
        result = get_earliest_national_team_debut(self.sample_player_data)
        
        # Should return the senior team debut in 2010 (not the U-21 in 2008)
        assert result is not None
        assert result["start_year"] == 2010
        assert result["name"] == "Spain men's national football team"

    def test_get_debut_years_distribution(self):
        """Test calculating debut year distribution."""
        result = get_debut_years_distribution(self.sample_all_data)
        
        # Should count the years correctly
        assert result[2010] == 2  # Two players debuted in 2010
        assert result[2008] == 1  # One player debuted in 2008

    def test_generate_realistic_distractor_years(self):
        """Test generating distractor years."""
        debut_years = {2008: 1, 2009: 2, 2010: 3, 2011: 1, 2012: 2}
        
        result = generate_realistic_distractor_years(2010, debut_years, 3)
        
        # Should return 3 different years, none of which is 2010
        assert len(result) == 3
        assert 2010 not in result
        assert all(isinstance(year, int) for year in result)

    def test_generate_debut_year_question(self):
        """Test generating a complete question."""
        debut_years = {2008: 1, 2009: 2, 2010: 3, 2011: 1, 2012: 2}
        
        result = generate_debut_year_question("Q1", self.sample_player_data, debut_years)
        
        # Should generate a complete question structure
        assert result is not None
        assert "question" in result
        assert "question_cantonese" in result
        assert "choices" in result
        assert "choices_cantonese" in result
        assert "correct_answer" in result
        assert result["correct_answer"] in ["A", "B", "C", "D"]
        
        # Check player information
        assert result["player_info"]["name"] == "Test Player"
        assert result["player_info"]["name_cantonese"] == "測試球員"
        
        # Check debut information
        assert result["debut_info"]["year"] == 2010
        assert result["debut_info"]["team_name"] == "Spain men's national football team"
        
        # Check that all choices are years
        all_choices = list(result["choices"].values())
        assert len(all_choices) == 4
        assert "2010" in all_choices  # Correct answer should be present
        
        # Check Cantonese choices have year suffix
        cantonese_choices = list(result["choices_cantonese"].values())
        assert all(choice.endswith("年") for choice in cantonese_choices)

    def test_no_national_teams(self):
        """Test handling player with no national teams."""
        player_data = {
            "player_names": {"english": "Test Player", "cantonese_best": "測試球員"},
            "national_teams": []
        }
        
        result = get_earliest_national_team_debut(player_data)
        assert result is None

    def test_no_debut_year_data(self):
        """Test handling player with national team but no start year."""
        player_data = {
            "player_names": {"english": "Test Player", "cantonese_best": "測試球員"},
            "national_teams": [
                {
                    "club_id": "Q42267",
                    "start_year": None,  # No start year data
                    "name": "Spain men's national football team",
                    "cantonese_name": "西班牙足球代表隊",
                    "description": "men's national association football team representing Spain"
                }
            ]
        }
        
        result = get_earliest_national_team_debut(player_data)
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__])
