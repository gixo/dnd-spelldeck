#!/usr/bin/env python3
"""
D&D Beyond Spell Parser
Extracts spell data from downloaded HTML pages and converts to JSON format.
"""

import os
import json
import re
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SpellParser:
    """Parser for D&D Beyond spell HTML pages."""
    
    def __init__(self, html_dir: str = "spell_pages", output_file: str = None):
        """
        Initialize the parser.
        
        Args:
            html_dir: Directory containing HTML files
            output_file: Output JSON file path
        """
        self.html_dir = Path(html_dir)
        self.output_file = output_file or self.html_dir.parent / "data" / "spells_parsed.json"
        self.spells = {}
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Strip leading/trailing whitespace
        text = text.strip()
        return text
    
    def _parse_level(self, level_str: str) -> int:
        """
        Parse spell level from string.
        
        Args:
            level_str: Level string like "1st", "2nd", "Cantrip"
            
        Returns:
            Integer level (0 for cantrip)
        """
        level_str = level_str.lower().strip()
        
        if 'cantrip' in level_str:
            return 0
        
        # Extract number from strings like "1st", "2nd", "3rd", etc.
        match = re.search(r'(\d+)', level_str)
        if match:
            return int(match.group(1))
        
        return 0
    
    def _parse_components(self, components_str: str) -> tuple[List[str], Optional[str]]:
        """
        Parse components string.
        
        Args:
            components_str: Components string like "V, S, M *"
            
        Returns:
            Tuple of (components_list, material_description)
        """
        if not components_str:
            return [], None
        
        components = []
        
        # Check for V, S, M
        if 'V' in components_str:
            components.append('V')
        if 'S' in components_str:
            components.append('S')
        if 'M' in components_str:
            components.append('M')
        
        return components, None  # Material description extracted separately
    
    def _parse_range_area(self, range_value_elem) -> str:
        """
        Parse range/area including extracting shape from icon.
        
        Args:
            range_value_elem: BeautifulSoup element containing range/area value
            
        Returns:
            Range/area string with shape (e.g., "Self (60 ft. cone)")
        """
        if not range_value_elem:
            return ""
        
        # Extract the area shape from icon if present
        aoe_icon = range_value_elem.find('i', class_=re.compile(r'i-aoe-'))
        if aoe_icon:
            # Extract shape from class like "i-aoe-cone" -> "cone"
            for cls in aoe_icon.get('class', []):
                if cls.startswith('i-aoe-'):
                    shape = cls.replace('i-aoe-', '')
                    # Replace the icon with the shape text
                    aoe_icon.replace_with(shape)
                    break
        
        return self._clean_text(range_value_elem.get_text())
    
    def _parse_classes(self, classes_html) -> List[str]:
        """
        Parse available classes from footer.
        
        Args:
            classes_html: BeautifulSoup element containing class tags
            
        Returns:
            List of class names
        """
        classes = []
        
        if not classes_html:
            return classes
        
        class_tags = classes_html.find_all('span', class_='tag')
        
        for tag in class_tags:
            class_text = self._clean_text(tag.get_text())
            
            # Extract main class name, handling subclasses and legacy tags
            # Examples: "Wizard (Legacy)", "Druid (Legacy) - Circle of the Land (Swamp) (Legacy)"
            
            # Remove " (Legacy)" tags
            class_text = re.sub(r'\s*\(Legacy\)', '', class_text)
            
            # Split by " - " to separate main class from subclass
            parts = class_text.split(' - ')
            main_class = parts[0].strip()
            
            if main_class and main_class not in classes:
                classes.append(main_class)
        
        return sorted(classes)
    
    def _parse_source(self, source_html) -> tuple[Optional[str], Optional[int]]:
        """
        Parse source book and page number.
        
        Args:
            source_html: BeautifulSoup element containing source info
            
        Returns:
            Tuple of (source_name, page_number)
        """
        if not source_html:
            return None, None
        
        source_text = self._clean_text(source_html.get_text())
        
        # Try to extract page number
        page_match = re.search(r'pg?\.\s*(\d+)', source_text, re.IGNORECASE)
        page_number = int(page_match.group(1)) if page_match else None
        
        # Remove page number from source name
        source_name = re.sub(r',?\s*pg?\.\s*\d+', '', source_text, flags=re.IGNORECASE).strip()
        
        return source_name or None, page_number
    
    def _convert_to_latex_formatting(self, html_content) -> str:
        """
        Convert HTML formatting to LaTeX formatting used by the card generator.
        
        Args:
            html_content: BeautifulSoup element with HTML content
            
        Returns:
            Formatted text string
        """
        if not html_content:
            return ""
        
        text_parts = []
        
        # Process each paragraph
        for p in html_content.find_all('p'):
            para_text = ""
            
            # Track if we've already processed an element
            processed_elements = set()
            
            # Process text nodes and formatting
            for element in p.descendants:
                # Skip if already processed as part of parent
                if id(element) in processed_elements:
                    continue
                    
                if element.name is None:  # Text node
                    para_text += element
                elif element.name == 'em':
                    # Check if it contains strong (for bold+italic)
                    strong = element.find('strong')
                    if strong:
                        # Bold+Italic text (em > strong)
                        text = self._clean_text(strong.get_text())
                        para_text += f"{{\\normalfont\\textbf{{{text}}}}}"
                        # Mark strong as processed
                        processed_elements.add(id(strong))
                        # Mark all descendants as processed
                        for desc in strong.descendants:
                            processed_elements.add(id(desc))
                    else:
                        # Just italic - treat as regular text for spell cards
                        para_text += self._clean_text(element.get_text())
                elif element.name == 'strong':
                    # Bold text
                    text = self._clean_text(element.get_text())
                    para_text += f"{{\\normalfont\\textbf{{{text}}}}}"
                    # Mark all descendants as processed
                    for desc in element.descendants:
                        processed_elements.add(id(desc))
            
            if para_text:
                text_parts.append(self._clean_text(para_text))
        
        return "\n\n".join(text_parts)
    
    def parse_spell_html(self, html_path: Path) -> Optional[Dict[str, Any]]:
        """
        Parse a single spell HTML file.
        
        Args:
            html_path: Path to HTML file
            
        Returns:
            Dictionary of spell data, or None if parsing fails
        """
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract spell name from page title
            spell_name = None
            title_elem = soup.find('h1', class_='page-title')
            if title_elem:
                spell_name = self._clean_text(title_elem.get_text())
            
            if not spell_name:
                logger.warning(f"Could not extract spell name from {html_path}, deleting file")
                html_path.unlink()  # Delete the invalid HTML file
                return None
            
            # Find the statblock
            statblock = soup.find('div', class_='ddb-statblock-spell')
            if not statblock:
                logger.warning(f"Could not find statblock in {html_path}")
                return None
            
            # Extract data from statblock
            spell_data = {}
            
            # Level
            level_elem = statblock.find('div', class_='ddb-statblock-item-level')
            if level_elem:
                level_value = level_elem.find('div', class_='ddb-statblock-item-value')
                spell_data['level'] = self._parse_level(level_value.get_text())
            
            # Casting Time
            time_elem = statblock.find('div', class_='ddb-statblock-item-casting-time')
            if time_elem:
                time_value = time_elem.find('div', class_='ddb-statblock-item-value')
                time_text = self._clean_text(time_value.get_text())
                
                # Check for ritual
                ritual_icon = time_value.find('i', class_='i-ritual')
                spell_data['ritual'] = ritual_icon is not None
                
                # Remove "Ritual" text from casting time
                time_text = re.sub(r'\s*Ritual\s*', '', time_text).strip()
                spell_data['time'] = time_text.lower()
            
            # Range/Area
            range_elem = statblock.find('div', class_='ddb-statblock-item-range-area')
            if range_elem:
                range_value = range_elem.find('div', class_='ddb-statblock-item-value')
                spell_data['range'] = self._parse_range_area(range_value)
            
            # Components
            comp_elem = statblock.find('div', class_='ddb-statblock-item-components')
            if comp_elem:
                comp_value = comp_elem.find('div', class_='ddb-statblock-item-value')
                comp_text = self._clean_text(comp_value.get_text())
                components, _ = self._parse_components(comp_text)
                spell_data['components'] = components
            
            # Duration
            dur_elem = statblock.find('div', class_='ddb-statblock-item-duration')
            if dur_elem:
                dur_value = dur_elem.find('div', class_='ddb-statblock-item-value')
                duration_text = self._clean_text(dur_value.get_text())
                
                # Check for concentration
                concentration = 'concentration' in duration_text.lower()
                spell_data['concentration'] = concentration
                
                # Remove "Concentration" from duration text
                duration_text = re.sub(r'Concentration,?\s*', '', duration_text, flags=re.IGNORECASE).strip()
                spell_data['duration'] = duration_text
            
            # School
            school_elem = statblock.find('div', class_='ddb-statblock-item-school')
            if school_elem:
                school_value = school_elem.find('div', class_='ddb-statblock-item-value')
                spell_data['school'] = self._clean_text(school_value.get_text())
            
            # Attack/Save
            attack_elem = statblock.find('div', class_='ddb-statblock-item-attack-save')
            if attack_elem:
                attack_value = attack_elem.find('div', class_='ddb-statblock-item-value')
                spell_data['attack_save'] = self._clean_text(attack_value.get_text())
            
            # Damage/Effect
            damage_elem = statblock.find('div', class_='ddb-statblock-item-damage-effect')
            if damage_elem:
                damage_value = damage_elem.find('div', class_='ddb-statblock-item-value')
                spell_data['damage_effect'] = self._clean_text(damage_value.get_text())
            
            # Description
            desc_elem = soup.find('div', class_='more-info-content')
            if desc_elem:
                # Convert HTML formatting to LaTeX
                spell_data['text'] = self._convert_to_latex_formatting(desc_elem)
                
                # Extract material components
                material_span = desc_elem.find('span', class_='components-blurb')
                if material_span:
                    material_text = self._clean_text(material_span.get_text())
                    # Remove "* - " and parentheses
                    material_text = re.sub(r'^\*\s*-\s*\(?(.*?)\)?$', r'\1', material_text)
                    spell_data['material'] = material_text if material_text else None
                else:
                    spell_data['material'] = None
            
            # Classes (from footer)
            footer = soup.find('footer')
            if footer:
                classes_elem = footer.find('p', class_='available-for')
                spell_data['classes'] = self._parse_classes(classes_elem)
                
                # Source
                source_elem = footer.find('p', class_='source')
                source_name, source_page = self._parse_source(source_elem)
                spell_data['source'] = source_name
                spell_data['source_page'] = source_page
            
            logger.info(f"Successfully parsed: {spell_name}")
            return spell_name, spell_data
            
        except Exception as e:
            logger.error(f"Error parsing {html_path}: {e}", exc_info=True)
            return None
    
    def parse_all_spells(self):
        """Parse all HTML files in the directory."""
        if not self.html_dir.exists():
            logger.error(f"Directory not found: {self.html_dir}")
            return
        
        html_files = list(self.html_dir.glob("*.html"))
        
        if not html_files:
            logger.warning(f"No HTML files found in {self.html_dir}")
            return
        
        logger.info(f"Found {len(html_files)} HTML files to parse")
        
        successful = 0
        failed = 0
        
        for html_file in html_files:
            result = self.parse_spell_html(html_file)
            
            if result:
                spell_name, spell_data = result
                self.spells[spell_name] = spell_data
                successful += 1
            else:
                failed += 1
        
        logger.info(f"\nParsing complete!")
        logger.info(f"Successfully parsed: {successful}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Total spells: {len(self.spells)}")
    
    def save_json(self):
        """Save parsed spells to JSON file."""
        # Create output directory if it doesn't exist
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Sort spells by name
        sorted_spells = dict(sorted(self.spells.items()))
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(sorted_spells, f, indent=4, ensure_ascii=False)
        
        logger.info(f"Saved {len(sorted_spells)} spells to {self.output_file}")
    
    def merge_with_existing(self, existing_file: str):
        """
        Merge parsed spells with existing JSON file.
        
        Args:
            existing_file: Path to existing spells.json
        """
        existing_path = Path(existing_file)
        
        if not existing_path.exists():
            logger.warning(f"Existing file not found: {existing_file}")
            return
        
        with open(existing_path, 'r', encoding='utf-8') as f:
            existing_spells = json.load(f)
        
        # Merge (new data takes precedence)
        merged = {**existing_spells, **self.spells}
        
        logger.info(f"Merged {len(self.spells)} new/updated spells with {len(existing_spells)} existing spells")
        logger.info(f"Total spells after merge: {len(merged)}")
        
        self.spells = merged


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Parse D&D Beyond spell HTML files into JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Parse all spells in spell_pages directory
  python spell_parser.py
  
  # Specify custom input/output
  python spell_parser.py --input my_spells --output spells_new.json
  
  # Merge with existing spells.json
  python spell_parser.py --merge ../data/spells.json
        """
    )
    
    parser.add_argument(
        '--input', '-i',
        default='spell_pages',
        help='Input directory containing HTML files (default: spell_pages)'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output JSON file (default: ../data/spells_parsed.json)'
    )
    
    parser.add_argument(
        '--merge', '-m',
        help='Merge with existing JSON file (e.g., ../data/spells.json)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create parser
    spell_parser = SpellParser(html_dir=args.input, output_file=args.output)
    
    # Parse all spells
    spell_parser.parse_all_spells()
    
    # Merge if requested
    if args.merge:
        spell_parser.merge_with_existing(args.merge)
    
    # Save to JSON
    if spell_parser.spells:
        spell_parser.save_json()
    else:
        logger.warning("No spells to save!")


if __name__ == '__main__':
    main()
