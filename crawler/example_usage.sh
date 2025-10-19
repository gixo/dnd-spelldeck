#!/bin/bash
# Example workflow for downloading and parsing D&D Beyond spells

echo "=== D&D Beyond Spell Crawler & Parser Example ==="
echo ""

# Step 1: Download spells (testing with just 5 spells)
echo "Step 1: Downloading spells from D&D Beyond..."
echo "Command: python3 spell_crawler.py --max-spells 5 --delay 2.0"
echo ""
# python3 spell_crawler.py --max-spells 5 --delay 2.0

# Alternative examples:
# Download only Core Rules spells:
# python3 spell_crawler.py --category core-rules --max-spells 10

# Download Core Rules and Expanded Rules spells:
# python3 spell_crawler.py -c core-rules -c expanded-rules --max-spells 10

# Download PHB spells from Core Rules category:
# python3 spell_crawler.py --source phb --category core-rules --max-spells 10

# Download all Critical Role spells:
# python3 spell_crawler.py --category critical-role

# Step 2: Parse the downloaded HTML files
echo "Step 2: Parsing downloaded HTML files..."
echo "Command: python3 spell_parser.py"
python3 spell_parser.py

# Step 3: Show the results
echo ""
echo "Step 3: Viewing parsed data..."
echo "First spell in parsed JSON:"
python3 -c "import json; data = json.load(open('data/spells_parsed.json')); print(json.dumps({list(data.keys())[0]: list(data.values())[0]}, indent=2))"

# Step 4: Optionally merge with existing data
echo ""
echo "Step 4: To merge with existing spells.json, run:"
echo "python3 spell_parser.py --merge ../data/spells.json --output ../data/spells.json"

echo ""
echo "=== Done! ==="
echo "Parsed spells saved to: data/spells_parsed.json"
echo "You can now use this JSON file with the card generator in ../generate.py"
