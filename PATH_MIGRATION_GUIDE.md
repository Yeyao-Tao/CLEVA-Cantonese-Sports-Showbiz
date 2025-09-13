# Path Utilities Migration Guide

## Summary

This document describes the migration from hardcoded relative paths to absolute paths using a new path utilities module.

## Problem

The codebase previously used hardcoded relative paths like:
```python
directory_path = "./data/soccer/intermediate/football_players_triples"
cache_dir = "./data/soccer/cantonese_name_mapping"
output_file = "./data/soccer/intermediate/football_players_clubs_complete.json"
```

These relative paths required scripts to be run from a specific directory (the project root), making the codebase less flexible and error-prone.

## Solution

### 1. Created Path Utilities Module

A new utility module `src/utils/path_utils.py` provides functions to get absolute paths:

- `get_project_root()` - Returns absolute path to project root
- `get_data_dir()` - Returns absolute path to data/ directory
- `get_soccer_data_dir()` - Returns absolute path to data/soccer/
- `get_soccer_intermediate_dir()` - Returns absolute path to data/soccer/intermediate/
- `get_soccer_output_dir()` - Returns absolute path to data/soccer/output/
- `get_soccer_raw_dir()` - Returns absolute path to data/soccer/raw/
- `get_cantonese_mapping_dir()` - Returns absolute path to data/soccer/cantonese_name_mapping/
- `get_football_players_triples_dir()` - Returns absolute path to data/soccer/intermediate/football_players_triples/

### 2. Updated Files

The following files have been **completely updated** to use absolute paths:

#### **Source Files (✅ COMPLETED):**
- ✅ `src/extract_all_clubs.py` - Complete migration from relative to absolute paths
- ✅ `src/extract_cantonese_names.py` - Updated main configuration paths  
- ✅ `src/extract_birth_years.py` - Updated all directory references
- ✅ `src/fifa_dataset_lookup.py` - Updated FIFA data file paths
- ✅ `src/extract_jersey_numbers.py` - Updated triples and output directories
- ✅ `src/wikidata_lookup.py` - Updated data file paths and constants
- ✅ `src/generate_birth_year_questions.py` - Updated input/output paths
- ✅ `src/generate_debut_year_questions.py` - Updated data file paths
- ✅ `src/generate_team_questions.py` - Updated input/output paths
- ✅ `src/generate_teammate_questions.py` - Updated data file paths

#### **Root Level Files (✅ COMPLETED):**
- ✅ `compare_yue_zh_hk.py` - Updated triples directory and output paths
- ✅ `cantonese_analysis.py` - Updated output file paths

## Migration Pattern for Remaining Files

To update the remaining files, follow this pattern:

### 1. Add import
```python
from utils.path_utils import (
    get_football_players_triples_dir,
    get_cantonese_mapping_dir,
    get_soccer_intermediate_dir,
    get_soccer_output_dir,
    get_soccer_raw_dir
)
```

### 2. Replace hardcoded paths

| Old Pattern | New Pattern |
|------------|-------------|
| `"./data/soccer/intermediate/football_players_triples"` | `get_football_players_triples_dir()` |
| `"./data/soccer/cantonese_name_mapping"` | `get_cantonese_mapping_dir()` |
| `"./data/soccer/intermediate/file.json"` | `os.path.join(get_soccer_intermediate_dir(), "file.json")` |
| `"./data/soccer/output/file.json"` | `os.path.join(get_soccer_output_dir(), "file.json")` |
| `"./data/soccer/raw/file.ext"` | `os.path.join(get_soccer_raw_dir(), "file.ext")` |
| `os.makedirs("./data/soccer/intermediate", exist_ok=True)` | `os.makedirs(get_soccer_intermediate_dir(), exist_ok=True)` |

## Files Still Needing Updates

Based on the search results, the following files still contain hardcoded relative paths:

### Test Files (⚠️ REMAINING):
- `tests/test_teammate_questions.py`
- `tests/unit/test_extract_birth_years.py`
- `tests/unit/test_extract_all_clubs.py`

### Data Files (ℹ️ INFORMATIONAL ONLY):
These contain paths as data, not as code to be executed:
- `data/soccer/cantonese_name_mapping/cantonese_extraction_stats.json`
- `data/soccer/intermediate/football_players_clubs_complete.json`

### Legacy Files (📁 ARCHIVED):
These appear to be duplicates in a soccer subfolder:
- `src/soccer/extract_birth_years.py`
- `tests/unit/soccer/test_extract_birth_years.py`

## Benefits

1. **Flexibility**: Scripts can now be run from any directory
2. **Reliability**: No more "file not found" errors due to incorrect working directory
3. **Maintainability**: Centralized path management
4. **Portability**: Easier to move or deploy the project

## Testing

The path utilities have been tested and confirmed to work correctly:
```bash
python -c "from src.utils.path_utils import *; print(get_data_dir())"
# Output: /Users/taoyeyao/workplace/CLEVA-Cantonese-Sports-Showbiz/data
```

All directory existence checks pass for the test environment. All updated source files have been tested and import successfully:

**✅ Successfully Updated & Tested:**
- All 10 main source files in `src/`
- All 2 root-level analysis files
- Path utilities module working correctly
- Scripts can now be run from any directory
- No import errors or path resolution issues
