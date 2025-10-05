# D&D Beyond Spell Crawler

A Python web crawler to download spell pages from D&D Beyond for personal use.

## ⚠️ Important Notice

Please respect D&D Beyond's Terms of Service and robots.txt. This crawler is intended for:
- **Personal/educational use only**
- **Not for redistribution or commercial use**
- **Consider supporting D&D Beyond** by purchasing official content

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Download all spells (with 2-second delay between requests):
```bash
python3 spell_crawler.py
```

### Testing

Download only 10 spells for testing:
```bash
python3 spell_crawler.py --max-spells 10
```

### Custom Configuration

Specify output directory and delay:
```bash
python3 spell_crawler.py --output my_spells --delay 3.0
```

### Command Line Options

- `--output`, `-o`: Output directory for HTML files (default: `spell_pages`)
- `--delay`, `-d`: Delay between requests in seconds (default: `2.0`)
- `--max-spells`, `-m`: Maximum number of spells to download
- `--source`, `-s`: Filter by source book (e.g., `phb`, `xge`, `tce`)
- `--verbose`, `-v`: Enable verbose logging

### Source Book Filtering

You can filter spells by source book using the `--source` flag:

```bash
# Download only Player's Handbook spells
python3 spell_crawler.py --source phb

# Download Xanathar's Guide to Everything spells
python3 spell_crawler.py --source xge

# Download Tasha's Cauldron of Everything spells
python3 spell_crawler.py --source tce
```

**Available Source Codes:**
- `phb`, `players-handbook` - Player's Handbook
- `xge`, `xanathars` - Xanathar's Guide to Everything
- `tce`, `tashas` - Tasha's Cauldron of Everything
- `scag` - Sword Coast Adventurer's Guide
- `eepc` - Elemental Evil Player's Companion
- `ftod`, `fizbans` - Fizban's Treasury of Dragons
- `basic`, `basic-rules` - Basic Rules
- `dmg` - Dungeon Master's Guide
- `explorers-guide` - Explorer's Guide to Wildemount
- `ggtr` - Guildmasters' Guide to Ravnica
- `ai` - Acquisitions Incorporated

Note: The crawler will check each spell's source information in the HTML to ensure it matches the specified source book.

## Features

- ✅ **Rate limiting**: Configurable delay between requests to be respectful
- ✅ **Progress tracking**: Resume interrupted downloads
- ✅ **Error handling**: Automatic retries with exponential backoff
- ✅ **Safe filenames**: Sanitizes spell names for filesystem compatibility
- ✅ **Logging**: Detailed progress information
- ✅ **Resumable**: Skips already-downloaded spells

## Output

The crawler creates:
- `spell_pages/` - Directory containing downloaded HTML files
- `spell_pages/progress.json` - Tracking file for resuming downloads

## Notes

- The crawler includes a 2-second default delay between requests to avoid overloading the server
- D&D Beyond uses pagination, so the crawler attempts to fetch multiple pages
- The page structure may change; you may need to adjust the CSS selectors if the crawler stops working
- Consider using the official D&D Beyond API if available for your use case

## Troubleshooting

If the crawler isn't finding spells:
1. Check if D&D Beyond's page structure has changed
2. Try running with `--verbose` flag for detailed logs
3. Test with `--max-spells 1` to see if a single spell works
4. The website may have changed their HTML structure - CSS selectors may need updating

## Parsing Downloaded Spells

After downloading spell HTML files, use the parser to extract data:

```bash
# Parse all downloaded spells
python3 spell_parser.py

# Parse and merge with existing spells.json
python3 spell_parser.py --merge ../data/spells.json

# Custom input/output
python3 spell_parser.py --input my_spells --output my_spells.json
```

The parser will:
- Extract all spell data from HTML pages
- Convert to JSON format compatible with the card generator
- Handle LaTeX formatting for special text (bold, etc.)
- Parse components, classes, level, school, and all other fields
- Support merging with existing spell databases

## Legal & Ethical Considerations

- Respect rate limits and don't overload the server
- This is for personal backup/reference only
- Content belongs to Wizards of the Coast
- Consider subscribing to D&D Beyond to support the creators
