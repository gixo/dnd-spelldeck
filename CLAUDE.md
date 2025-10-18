# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a D&D spell card generator that creates printable spell cards from D&D 5e spell data. The system converts spell data from JSON format into LaTeX documents that compile to PDF cards suitable for printing and cutting to Magic: The Gathering card size (8.89x6.35cm).

## Architecture

### Core Components

- **generate.py**: Main spell generation script that reads JSON data and outputs LaTeX format
- **generate_cards.py**: Wrapper script that orchestrates the full pipeline from JSON to PDF
- **data/spells.json**: Complete D&D 5e spell database (488KB)
- **tex/cards.tex**: LaTeX template for individual spell cards
- **tex/printable.tex**: LaTeX template for arranging cards on printable sheets
- **tex/spells.tex**: Generated LaTeX file containing all selected spells (created by scripts)

### Key Features

- **Spell Filtering**: By class, level, school, or name
- **Spell Sorting**: By name (alphabetically) or by level (grouped by level, then alphabetically)
- **Text Truncation**: Automatically truncates long spell descriptions to fit cards (MAX_TEXT_LENGTH = 670)
- **Area Effect Icons**: Displays cube/emanation icons for spells with area effects
- **Concentration Indicators**: Visual indicators for concentration spells
- **Font Support**: Uses Mrs Eaves font when available (XeLaTeX), falls back to default LaTeX font

## Common Commands

### Generate spell cards
```bash
# Generate all spells
python3 generate_cards.py

# Generate specific classes
python3 generate_cards.py -c wizard -c sorcerer

# Generate specific levels (supports ranges)
python3 generate_cards.py -l 1-3

# Sort spells by level (default is alphabetical by name)
python3 generate_cards.py --sort-by level

# Combine filters and sorting
python3 generate_cards.py -c wizard -l 1-3 --sort-by level

# Generate and clean up intermediate files
python3 generate_cards.py --clean

# Only generate LaTeX without compiling to PDF
python3 generate_cards.py --no-compile
```

### Manual LaTeX compilation
```bash
# Compile LaTeX files manually
latexmk -xelatex -shell-escape -cd tex/cards.tex tex/printable.tex
```

### Run tests
```bash
python3 tests.py
```

## Dependencies

### Required
- **Python 3.6+**
- **LaTeX**: XeLaTeX recommended, standard LaTeX as fallback
- **latexmk**: LaTeX build tool
- **Inkscape**: Required for SVG area effect icons (must be in PATH)

### Optional
- **Mrs Eaves font**: For authentic D&D styling (proprietary font)

## Development Notes

### Text Processing
- Spell text is automatically wrapped to 80 characters per line
- Text exceeding MAX_TEXT_LENGTH (670 chars) is truncated with "..."
- Double newlines in source text are preserved as paragraph breaks
- Material components are automatically appended with "* - (" prefix

### LaTeX Template System
- **cards.tex**: Contains the spell card environment and styling
- **printable.tex**: Simple wrapper that arranges cards 3x3 on A4 paper
- Cards use background images from `images/` directory
- SVG icons processed via Inkscape (requires -shell-escape flag)

### File Organization
- Generated PDFs are moved to `pdf/` directory by default
- LaTeX intermediate files remain in `tex/` directory
- Use `--clean` flag to remove intermediate files after generation