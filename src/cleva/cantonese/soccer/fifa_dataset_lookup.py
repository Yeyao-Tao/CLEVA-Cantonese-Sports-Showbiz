import pandas as pd
import os
import sys

from cleva.cantonese.utils.path_utils import get_soccer_raw_dir, get_soccer_intermediate_dir

def get_names_from_FC24(file_path: str, min_overall: int = 85) -> list[str]:
    # Read the data with both long_name and overall columns
    df = pd.read_csv(file_path, usecols=["long_name", "overall"])
    
    # Remove rows with missing data
    df = df.dropna()
    
    # Strip whitespace from names
    df["long_name"] = df["long_name"].str.strip()
    
    # Filter players who have overall > min_overall in at least one FIFA version
    # Group by player name and check if any version has overall > min_overall
    qualified_players = df.groupby("long_name")["overall"].max() > min_overall
    qualified_names = qualified_players[qualified_players].index.tolist()
    
    return qualified_names


if __name__ == "__main__":
    min_overall = 85
    fifa_file = os.path.join(get_soccer_raw_dir(), "FC24", "male_players.csv")
    names = get_names_from_FC24(fifa_file, min_overall)
    print(f"Players with overall > {min_overall}: {len(names)}")
    print(f"First player: {names[0]}")
    
    # Create output directory if it doesn't exist
    output_dir = get_soccer_intermediate_dir()
    os.makedirs(output_dir, exist_ok=True)
    
    # Save names to file
    output_file = os.path.join(output_dir, "fifa_player_names.txt")
    with open(output_file, 'w', encoding='utf-8') as f:
        for name in names:
            f.write(f"{name}\n")
    
    print(f"Saved {len(names)} player names to {output_file}")