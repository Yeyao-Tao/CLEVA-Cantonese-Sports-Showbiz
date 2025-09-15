# Movie Name Extraction from Lua Files

This directory contains scripts for extracting movie names from MediaWiki CGroup Lua files.

## Files

### Scripts
- `movie_extractor.py` - Combined extraction script that reads the Lua file and generates both detailed and simple output formats

### Output Files (in `data/entertainment/intermediate/`)
- `movies_english_cantonese.json` - Detailed extraction with metadata (4,590 movies)
- `movies_simple_english_cantonese.json` - Simple English -> Cantonese mapping (4,565 movies)

## Extraction Process

The `movie_extractor.py` script:

1. **Parses Lua File**: Reads `/data/entertainment/raw/cgroup_movie.lua`
2. **Extracts Movie Items**: Finds `Item()` function calls containing movie translations
3. **Filters Non-Movies**: Stops processing when reaching sections like:
   - Film festivals and awards (`==電影節及相關獎項==`)
   - Studios and companies (`==製片廠及相關業者==`)
   - Technical terms (`==其他==`)
   - Character conversions (`==繁簡轉換==`)
4. **Extracts Names**: Parses English names and Cantonese (`zh-hk`) translations
5. **Saves Results**: Outputs both detailed and simple JSON formats simultaneously

## Data Quality

- **Total Items Processed**: 4,590 movie entries
- **Filtering**: Only includes movies with both English and Cantonese (zh-hk) names
- **Source**: MediaWiki CGroup conversion rules from Chinese Wikipedia
- **Language Coverage**: Focuses on Hong Kong Cantonese (`zh-hk`) translations

## Usage

Run the combined extraction script:
```bash
python src/cleva/cantonese/entertainment/movie_extractor.py
```

This single command will:
- Extract all movie data from the Lua file
- Generate both detailed and simple JSON formats
- Save results to the intermediate directory

## Example Output

```json
{
  "english_name": "10 Cloverfield Lane",
  "cantonese_name": "末世街10號",
  "line_number": 15
}
```

Simple format:
```json
{
  "10 Cloverfield Lane": "末世街10號"
}
```
