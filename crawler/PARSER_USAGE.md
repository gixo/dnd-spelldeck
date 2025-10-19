# Spell Parser Usage Guide

The spell parser extracts spell data from downloaded D&D Beyond HTML pages and converts it to JSON format compatible with your card generator.

## Features

✅ **Complete Data Extraction**
- Spell name, level, school, casting time
- Components (V, S, M) with material descriptions
- Range, duration, concentration flag
- Ritual flag, attack/save type, damage/effect
- Full spell description with LaTeX formatting
- Available classes and source book information

✅ **Smart Formatting**
- Converts HTML bold/italic to LaTeX formatting
- Preserves paragraph breaks
- Handles "At Higher Levels" sections properly
- Compatible with existing `generate.py` card generator

✅ **Flexible Options**
- Parse all spells or specific directories
- Merge with existing spell databases
- Custom output paths
- Verbose logging for debugging

## Quick Start

```bash
# 1. Parse all spells from spell_pages/in_source (works from any directory)
cd /path/to/dnd-spellcheck-gixo
python3 crawler/spell_parser.py

# 2. View the output (saved to crawler/data/spells_parsed.json)
cat crawler/data/spells_parsed.json

# 3. Merge with existing spells.json
python3 crawler/spell_parser.py --output data/spells.json
```

## Output Format

The parser generates JSON matching the format expected by `generate.py`:

```json
{
    "Spell Name": {
        "level": 1,
        "school": "Abjuration",
        "time": "1 action",
        "range": "Self",
        "components": ["V", "S"],
        "duration": "1 round",
        "ritual": false,
        "concentration": false,
        "material": null,
        "text": "Spell description with {\\normalfont\\textbf{Bold Text}}...",
        "classes": ["Artificer", "Druid", "Wizard"],
        "source": "Player's Handbook",
        "source_page": 239,
        "attack_save": "None",
        "damage_effect": "Buff"
    }
}
```

## Field Mapping

| HTML Source | JSON Field | Notes |
|-------------|------------|-------|
| Page Title | Key name | Spell name |
| Level statblock | `level` | 0 for cantrips |
| Casting Time | `time` | Lowercase, ritual flag extracted |
| Range/Area | `range` | Full text including area |
| Components | `components` | Array: ["V", "S", "M"] |
| Duration | `duration` | Concentration flag extracted |
| School | `school` | School name |
| Attack/Save | `attack_save` | Attack type or save |
| Damage/Effect | `damage_effect` | Damage type or effect |
| Description paragraphs | `text` | LaTeX formatted |
| Material blurb | `material` | Text without asterisk |
| Available For tags | `classes` | Main classes only |
| Source footer | `source` | Source book name |
| Source footer | `source_page` | Page number if present |
| Ritual icon | `ritual` | Boolean |
| Duration text | `concentration` | Boolean |

## Command Line Options

```bash
python3 spell_parser.py [OPTIONS]

Options:
  --input, -i PATH      Input directory with HTML files 
                        (default: spell_pages/in_source relative to script location)
  --output, -o PATH     Output JSON file path 
                        (default: data/spells_parsed.json relative to script location)
  --merge, -m PATH      Merge with existing JSON file
  --verbose, -v         Enable verbose logging
  --help               Show help message

Note: Default paths are always relative to the script's location, regardless of where you call it from.
```

## Examples

### Parse and Save
```bash
# Parse all spells from spell_pages/in_source/ (saves to crawler/data/spells_parsed.json)
# Works from any directory!
python3 crawler/spell_parser.py

# Parse spells from not_in_source directory (relative to script location)
python3 crawler/spell_parser.py --input spell_pages/not_in_source

# Save directly to project's data folder
python3 crawler/spell_parser.py --output ../data/spells.json

# Use absolute paths for full control
python3 crawler/spell_parser.py --input /absolute/path/to/spells --output /absolute/path/to/output.json
```

### Merge with Existing Data
```bash
# Merge with existing and save to new file
python3 crawler/spell_parser.py --merge ../data/spells_old.json --output ../data/spells_new.json

python3 crawler/spell_parser.py --input spell_pages/all_spells  -m ../data/spells_expanded.json --output ../data/spells.json
```

### Debug Parsing Issues
```bash
# Enable verbose logging to see detailed parsing info
python3 crawler/spell_parser.py --verbose
```

## Testing Parsed Data

Verify the parsed spells work with the card generator:

```bash
# Parse directly to the main data directory (backup first!)
cp data/spells.json data/spells_backup.json
python3 crawler/spell_parser.py --output data/spells.json

# Generate a test card
python3 generate.py --name "Acid Arrow" > tex/test_spell.tex

# Or generate cards for all parsed spells
python3 generate_cards.py
```

## Troubleshooting

### Issue: "Could not extract spell name"
- The HTML structure may have changed
- Try viewing the HTML file to check if it has the expected structure
- Look for `<h1 class="page-title">` element

### Issue: Missing fields in output
- Enable verbose logging: `python3 spell_parser.py --verbose`
- Check if the HTML has the expected CSS classes
- D&D Beyond may have updated their page structure

### Issue: Formatting looks wrong
- The parser converts HTML to LaTeX formatting
- Bold text becomes `{\normalfont\textbf{Text}}`
- This matches the format in the original `spells.json`

## Complete Workflow

1. **Download spells:**
   ```bash
   cd /path/to/dnd-spellcheck-gixo
   python3 crawler/spell_crawler.py --max-spells 10
   ```

2. **Parse HTML files:**
   ```bash
   # From anywhere - saves to crawler/data/spells_parsed.json
   python3 crawler/spell_parser.py
   ```

3. **Review parsed data:**
   ```bash
   python3 -c "import json; print(json.dumps(json.load(open('crawler/data/spells_parsed.json')), indent=2))" | less
   ```

4. **Copy to main data folder:**
   ```bash
   # Or parse directly to the main data folder
   python3 crawler/spell_parser.py --output data/spells.json
   ```

5. **Generate cards:** 
   ```bash
   python3 generate_cards.py
   ```

## Notes

- The parser preserves all LaTeX formatting from the original spell descriptions
- Material components are extracted from the "* - (material)" footnotes
- Classes include only main classes (subclasses are removed)
- The "Legacy" tag is stripped from class names
- Concentration is detected from the duration field
- Ritual is detected from the casting time icons
