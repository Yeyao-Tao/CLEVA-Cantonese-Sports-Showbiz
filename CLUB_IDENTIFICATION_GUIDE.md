# How to Identify a Football Player's Club from WikiData JSONLD Files

## Overview

In the WikiData JSONLD files for football players, club information is stored using the **P54** property, which represents "member of sports team". This guide explains how to extract this information systematically.

## Key WikiData Properties

1. **P54** - "member of sports team" - The main property for club memberships
2. **P580** - "start time" - When the player joined the club  
3. **P582** - "end time" - When the player left the club (absent for current clubs)

## Data Structure in JSONLD

### 1. Simple Club List
In the main player entity (e.g., `wd:Q96072055` for Musiala), you'll find:
```json
{
  "@id": "wd:Q96072055",
  "P54": [
    "wd:Q994701",  // FC Bayern Munich II
    "wd:Q15789"    // FC Bayern Munich  
  ]
}
```

### 2. Detailed Club Statements
More detailed information is stored in separate statement objects:
```json
{
  "@id": "wds:Q96072055-feb3fcf4-4424-726a-2492-09aa9db3bc42",
  "@type": ["wikibase:Statement", "wikibase:BestRank"],
  "ps:P54": "wd:Q994701",           // Club ID
  "P580": "2020-01-01T00:00:00Z",   // Start date
  "P582": "2020-01-01T00:00:00Z"    // End date
}
```

### 3. Club Information
Club names and descriptions are stored separately:
```json
{
  "@id": "wd:Q15789",
  "@type": "wikibase:Item",
  "label": {
    "@language": "en",
    "@value": "FC Bayern Munich"
  },
  "description": {
    "@language": "en", 
    "@value": "association football club in Munich, Germany"
  }
}
```

## Algorithm to Extract Club Information

### Step 1: Find the Player Entity
Look for items with:
- `@id` starting with `wd:Q` (not `wd:P` which are properties)
- `@type` = `"wikibase:Item"`
- Contains `P54` property

### Step 2: Extract Basic Club IDs
From the `P54` array, collect all club IDs (remove `wd:` prefix).

### Step 3: Find Detailed Club Statements
Look for items with:
- `@type` containing `"wikibase:Statement"`
- Contains `ps:P54` property
- Extract `P580` (start time) and `P582` (end time)

### Step 4: Determine Current vs Former Clubs
- **Current clubs**: No `P582` (end time) or `P582` has a blank node ID starting with `_:`
- **Former clubs**: Has a valid `P582` date

### Step 5: Get Club Names
Find items with:
- `@id` matching the club IDs from steps 2-3
- `@type` = `"wikibase:Item"`
- Extract `label` and `description`

## Example Results

For Jamal Musiala (Q96072055):
- **Current Club**: FC Bayern Munich (Q15789) - 2020 to present
- **Former Club**: FC Bayern Munich II (Q994701) - 2020 (same year, reserve team)

## Implementation Notes

1. **Date Parsing**: Dates are in ISO format (`YYYY-MM-DDTHH:MM:SSZ`)
2. **Multiple Languages**: Labels can exist in multiple languages
3. **Data Types**: Some fields may be objects, lists, or strings - handle accordingly
4. **Blank Nodes**: End dates with `_:` prefixes indicate ongoing memberships

## Common Patterns

- **Youth to Senior**: Players often move from reserve teams (II, B teams) to main teams
- **Loan Periods**: Short-term memberships with start and end dates in the same year
- **Multiple Clubs**: Professional players typically have multiple P54 statements
- **National Teams**: Also included in P54 but usually distinguishable by description

This structure allows you to build a complete picture of a player's career trajectory and current club status.
