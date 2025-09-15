# How to Read Lua Movie Data with Python

This guide explains how to parse the `cgroup_movie.lua` file containing movie names in English and various Chinese variants.

## File Structure

The Lua file contains movie translation data in the following format:

```lua
Item('English Movie Name', 'zh-tw:Traditional Chinese;zh-cn:Simplified Chinese;zh-hk:Cantonese;')
```

Example:
```lua
Item('Titanic', 'zh:泰坦尼克號;zh-cn:泰坦尼克号;zh-hk:鐵達尼號;zh-tw:鐵達尼號;')
```

## Language Codes

The file uses these language codes:
- `zh-cn`: Simplified Chinese (Mainland China)
- `zh-tw`: Traditional Chinese (Taiwan)
- `zh-hk`: Cantonese (Hong Kong)
- `zh-sg`: Chinese (Singapore)
- `zh-my`: Chinese (Malaysia)
- `zh-mo`: Chinese (Macau)
- `zh`: Generic Chinese
- `zh-hant`: Traditional Chinese characters
- `zh-hans`: Simplified Chinese characters

## Python Parsing Solutions

### 1. Simple Parser (`simple_lua_parser.py`)

A minimal script that extracts movie names and translations:

```python
import re
import json

def parse_lua_movies(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    pattern = r"Item\('([^']+)',\s*'([^']+)'"
    matches = re.findall(pattern, content)
    
    movies = {}
    for english_name, translation_rules in matches:
        if not english_name:
            continue
            
        translations = {}
        for rule in translation_rules.split(';'):
            if ':' in rule:
                if '=>' in rule:
                    rule = rule.split('=>')[-1]
                if ':' in rule:
                    lang_code, translation = rule.split(':', 1)
                    translations[lang_code.strip()] = translation.strip()
        
        movies[english_name] = translations
    
    return movies
```

### 2. Full-Featured Parser (`lua_parser.py`)

A complete class-based parser with additional methods:

```python
class LuaMovieParser:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.movies = []
    
    def parse_file(self) -> List[Dict]:
        # Parse and return structured data
        
    def get_cantonese_names(self) -> List[Tuple[str, str]]:
        # Extract English-Cantonese pairs
        
    def save_to_json(self, output_path: str):
        # Save data to JSON
```

## Usage Examples

### Basic Usage

```python
# Parse the file
movies = parse_lua_movies('path/to/cgroup_movie.lua')

# Get Cantonese translations
cantonese_movies = {}
for english_name, translations in movies.items():
    if 'zh-hk' in translations:
        cantonese_movies[english_name] = translations['zh-hk']

# Search for specific movies
titanic_translations = movies.get('Titanic', {})
print(titanic_translations)
# Output: {'zh': '泰坦尼克號', 'zh-cn': '泰坦尼克号', 'zh-hk': '鐵達尼號', ...}
```

### Search and Filter

```python
# Find movies with specific keywords
star_wars_movies = [name for name in movies if 'Star Wars' in name]

# Find movies with Chinese characters in Cantonese names
love_movies = []
for english, translations in movies.items():
    if 'zh-hk' in translations and '愛' in translations['zh-hk']:
        love_movies.append((english, translations['zh-hk']))
```

### Export to Different Formats

```python
# Save as JSON
import json
with open('movies.json', 'w', encoding='utf-8') as f:
    json.dump(movies, f, ensure_ascii=False, indent=2)

# Save as CSV
import csv
with open('movies.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['English', 'Cantonese', 'Traditional', 'Simplified'])
    
    for english, translations in movies.items():
        row = [
            english,
            translations.get('zh-hk', ''),
            translations.get('zh-tw', ''),
            translations.get('zh-cn', '')
        ]
        writer.writerow(row)
```

## Data Statistics

From the parsed file:
- **5,118 total movies** with translations
- **4,476 movies** have Cantonese (Hong Kong) translations
- **4,695 movies** have Simplified Chinese translations
- **4,653 movies** have Traditional Chinese translations

## Generated Files

Running the parsers will create:

1. `movies_simple_all.json` - All movies with all language variants
2. `movies_simple_cantonese.json` - English-Cantonese pairs only
3. `movies_2010s.json` - Movies with years 2010-2019 in titles
4. `movies_superhero.json` - Superhero movies (keyword-based)

## Key Features

- **Multiple language variants**: Extract translations for different Chinese variants
- **Cantonese focus**: Special handling for Hong Kong Cantonese translations
- **Search capabilities**: Find movies by English names or Chinese characters
- **Export options**: Save data in JSON, CSV, or custom formats
- **Pattern matching**: Find movies by year, genre keywords, etc.

## Common Use Cases

1. **Building bilingual databases**: Create English-Chinese movie databases
2. **Translation research**: Study how movie titles are translated across regions
3. **Cantonese language processing**: Extract Cantonese movie names for NLP tasks
4. **Cultural studies**: Analyze regional differences in movie title translations
5. **Data integration**: Combine with other movie databases using English names as keys

## Error Handling

The parsers handle:
- Empty movie names (skipped)
- Malformed translation rules
- Multiple translation formats (`=>` vs direct mapping)
- Missing language variants
- Unicode characters in Chinese text

## Running the Scripts

```bash
# Run the simple parser
python simple_lua_parser.py

# Run the full-featured parser
python lua_parser.py

# Run the analysis demo
python demo_movie_analysis.py
```

This approach gives you flexible access to the rich multilingual movie data contained in the Lua file format.
