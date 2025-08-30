# Cantonese Label Filter Implementation

## Overview
Added a comprehensive filter to identify football players who have Cantonese labels in their Wikidata records. This filter checks JSON-LD data for any content with the language code "yue" (Cantonese).

## Key Functions Added

### 1. `has_cantonese_label(jsonld_data)`
- **Purpose**: Checks if JSON-LD data contains any Cantonese (yue) labels
- **Logic**: Searches through the `@graph` structure for items with `"@language": "yue"`
- **Coverage**: Checks multiple fields including `name`, `inLanguage`, and any nested objects/arrays

### 2. `filter_players_with_cantonese_labels(saved_files)`
- **Purpose**: Filters a collection of JSON-LD files to separate players with/without Cantonese labels
- **Returns**: Two dictionaries - players with Cantonese labels and players without

### 3. `filter_existing_players_for_cantonese(input_dir)`
- **Purpose**: Standalone function to filter existing JSON-LD files
- **Usage**: Can be called independently to analyze already downloaded data

## Implementation Details

### JSON-LD Structure Analyzed
The filter looks for Cantonese content in structures like:
```json
{
  "@language": "yue",
  "@value": "美斯"
}
```

### Integration with Main Workflow
Modified the main execution flow in `wikidata_lookup.py` to:
1. Fetch all player data as before
2. Apply Cantonese filtering
3. Report detailed statistics
4. Save list of players with Cantonese labels to file

## Results Summary

### Test Run Results (Current Dataset)
- **Total players processed**: 149 JSON-LD files
- **Players with Cantonese labels**: 119 (79.9%)
- **Players without Cantonese labels**: 30 (20.1%)

### Example Cantonese Names Found
- Q615 (Messi): "美斯", "利安奴·美斯", "亞根庭足球員"
- Q142794 (Neymar): "尼馬"
- Q11571 (Cristiano Ronaldo): "基斯坦奴朗拿度", "葡萄牙足球員"
- Q129027 (Pogba): "普巴"
- Q1354960 (Salah): "穆罕默德·沙拿", "沙拿"

## Output Files Generated
1. **`./data/intermediate/players_with_cantonese_labels.txt`** - Simple list of Q-IDs with Cantonese labels
2. **`./data/intermediate/cantonese_players_detailed.txt`** - Detailed list with actual Cantonese names

## Usage Examples

### Run Full Pipeline with Cantonese Filtering
```bash
python src/wikidata_lookup.py
```

### Filter Existing Data Only
```bash
python test_cantonese_filter.py
```

### Detailed Analysis with Names
```bash
python cantonese_analysis.py
```

## Technical Notes

### Language Code
- Uses ISO 639-3 code "yue" for Cantonese
- This is the standard code used by Wikidata for Cantonese (Yue Chinese)

### Robustness
- Handles various JSON-LD structures (objects, arrays, nested items)
- Error handling for malformed files
- Comprehensive search across all graph items

### Performance
- Processes 149 files in approximately 10-15 seconds
- Memory efficient - processes one file at a time
- Can be easily parallelized if needed

## Future Enhancements

1. **Additional Language Filters**: Easy to extend for other Chinese variants (Mandarin, Wu, Min, etc.)
2. **Name Extraction**: Could be enhanced to extract and normalize Cantonese names
3. **Quality Scoring**: Could rank players by richness of Cantonese content
4. **Cross-Reference**: Could match with original FIFA names to find translation patterns
