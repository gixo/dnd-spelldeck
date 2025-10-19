#!/usr/bin/env python3
"""
D&D Beyond Spell Crawler
Downloads spell pages from dndbeyond.com for personal use.

IMPORTANT: Please respect D&D Beyond's Terms of Service and robots.txt.
This script is for educational/personal use only. Consider supporting D&D Beyond
by purchasing official content.
"""

import os
import time
import json
import logging
import argparse
from pathlib import Path
from urllib.parse import urljoin, urlparse
from typing import List, Set

import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SpellCrawler:
    """Crawler for downloading D&D Beyond spell pages."""
    
    BASE_URL = "https://www.dndbeyond.com"
    SPELLS_URL = "https://www.dndbeyond.com/spells"
    
    # Source book filter mapping: shorthand -> (numeric_id, full_name)
    # Numeric IDs match the filter-source select options on dndbeyond.com
    SOURCE_FILTERS = {
        # Core rulebooks
        'phb': (2, "Player's Handbook (2014)"),
        'players-handbook': (2, "Player's Handbook (2014)"),
        'phb-2024': (145, "Player's Handbook"),
        'dmg': (3, "Dungeon Master's Guide (2014)"),
        'dmg-2024': (146, "Dungeon Master's Guide"),
        'mm': (5, "Monster Manual (2014)"),
        'monster-manual': (5, "Monster Manual (2014)"),
        'mm-2024': (147, "Monster Manual"),
        'basic': (1, "Basic Rules (2014)"),
        'basic-rules': (1, "Basic Rules (2014)"),
        'basic-2024': (148, "D&D Beyond Basic Rules"),
        
        # Popular expansions
        'xge': (27, "Xanathar's Guide to Everything"),
        'xanathars': (27, "Xanathar's Guide to Everything"),
        'tce': (67, "Tasha’s Cauldron of Everything"),
        'tashas': (67, "Tasha’s Cauldron of Everything"),
        'ftod': (81, "Fizban's Treasury of Dragons"),
        'fizbans': (81, "Fizban's Treasury of Dragons"),
        'scag': (13, "Sword Coast Adventurer's Guide"),
        'eepc': (4, "Elemental Evil Player's Companion"),
        'vgtm': (15, "Volo's Guide to Monsters"),
        'volos': (15, "Volo's Guide to Monsters"),
        'mtof': (33, "Mordenkainen's Tome of Foes"),
        'mordenkainens': (33, "Mordenkainen's Tome of Foes"),
        'mpmm': (85, "Mordenkainen Presents: Monsters of the Multiverse"),
        
        # Campaign settings
        'ggtr': (38, "Guildmasters' Guide to Ravnica"),
        'ravnica': (38, "Guildmasters' Guide to Ravnica"),
        'egtw': (59, "Explorer's Guide to Wildemount"),
        'explorers-guide': (59, "Explorer's Guide to Wildemount"),
        'wildemount': (59, "Explorer's Guide to Wildemount"),
        'mot': (61, "Mythic Odysseys of Theros"),
        'theros': (61, "Mythic Odysseys of Theros"),
        'erlw': (49, "Eberron: Rising from the Last War"),
        'eberron': (49, "Eberron: Rising from the Last War"),
        'scc': (80, "Strixhaven: A Curriculum of Chaos"),
        'strixhaven': (80, "Strixhaven: A Curriculum of Chaos"),
        'vrgtr': (69, "Van Richten's Guide to Ravenloft"),
        'ravenloft': (69, "Van Richten's Guide to Ravenloft"),
        'tcsr': (123, "Tal'Dorei Campaign Setting Reborn"),
        'taldorei': (123, "Tal'Dorei Campaign Setting Reborn"),
        
        # Adventures with spells
        'ai': (44, "Acquisitions Incorporated"),
        'acquisitions': (44, "Acquisitions Incorporated"),
        'bgdia': (48, "Baldur's Gate: Descent into Avernus"),
        'idrotf': (66, "Icewind Dale: Rime of the Frostmaiden"),
        'cos': (6, "Curse of Strahd"),
        'wbtw': (79, "The Wild Beyond the Witchlight"),
        'sato': (90, "Spelljammer: Adventures in Space"),
        'spelljammer': (90, "Spelljammer: Adventures in Space"),
        'jttrc': (87, "Journeys through the Radiant Citadel"),
        'dsotdq': (95, "Dragonlance: Shadow of the Dragon Queen"),
        'dragonlance': (95, "Dragonlance: Shadow of the Dragon Queen"),
        'kftgv': (103, "Keys from the Golden Vault"),
        'bgpgg': (110, "Bigby Presents: Glory of the Giants"),
        'pbtso': (113, "Phandelver and Below: The Shattered Obelisk"),
        'paitm': (114, "Planescape: Adventures in the Multiverse"),
        'planescape': (114, "Planescape: Adventures in the Multiverse"),
        'tbmt': (109, "The Book of Many Things"),
        'qftis': (137, "Quests from the Infinite Staircase"),
        'veor': (132, "Vecna: Eve of Ruin"),
        
        # Third-party content
        'humblewood': (133, "Humblewood Campaign Setting"),
        'dod': (131, "Dungeons of Drakkenheim"),
        'drakkenheim': (131, "Dungeons of Drakkenheim"),
    }
    
    def __init__(self, output_dir: str = "crawler/spell_pages", delay: float = 1.0, 
                 source_filter: str = None, cookies: dict = None):
        """
        Initialize the crawler.
        
        Args:
            output_dir: Directory to save HTML files
            delay: Delay between requests in seconds (be respectful!)
            source_filter: Optional source book filter (e.g., 'phb', 'xge', 'tce')
            cookies: Optional dictionary of cookies for authenticated requests
        """
        self.base_dir = Path(output_dir)
        self.base_dir.mkdir(exist_ok=True)
        self.delay = delay
        self.source_filter = source_filter
        
        # Create subdirectory for inaccessible spells
        self.unaccessible_dir = self.base_dir / "unaccessible"
        self.unaccessible_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for filtered sources
        if source_filter:
            self.output_dir = self.base_dir / "in_source"
            self.other_sources_dir = self.base_dir / "not_in_source"
            self.output_dir.mkdir(exist_ok=True)
            self.other_sources_dir.mkdir(exist_ok=True)
        else:
            # No filter: save everything to base directory
            self.output_dir = self.base_dir
            self.other_sources_dir = None
        
        # Track progress
        self.progress_file = self.base_dir / "progress.json"
        self.downloaded_urls, self.skipped_urls, self.all_spell_urls = self._load_progress()
        
        # Session with headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        
        # Add cookies if provided
        if cookies:
            self.session.cookies.update(cookies)
    
    def _load_progress(self) -> tuple[Set[str], Set[str], List[str]]:
        """Load previously downloaded, skipped, and discovered URLs from progress file."""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r') as f:
                    data = json.load(f)
                    downloaded = set(data.get('downloaded', []))
                    skipped = set(data.get('skipped', []))
                    all_urls = data.get('all_spell_urls', [])
                    return downloaded, skipped, all_urls
            except Exception as e:
                logger.warning(f"Could not load progress file: {e}")
        return set(), set(), []
    
    def _save_progress(self):
        """Save progress to file."""
        try:
            with open(self.progress_file, 'w') as f:
                json.dump({
                    'all_spell_urls': self.all_spell_urls,
                    'downloaded': sorted(list(self.downloaded_urls)),
                    'skipped': sorted(list(self.skipped_urls))
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save progress: {e}")
    
    def _get_page(self, url: str, retries: int = 3) -> requests.Response:
        """
        Fetch a page with retry logic.
        
        Args:
            url: URL to fetch
            retries: Number of retries on failure
            
        Returns:
            Response object
        """
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                time.sleep(self.delay)  # Be respectful with rate limiting
                return response
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < retries - 1:
                    time.sleep(self.delay * 2)  # Wait longer on errors
                else:
                    raise
    
    def _sanitize_filename(self, name: str) -> str:
        """Convert spell name/URL to safe filename."""
        # Remove special characters and replace spaces
        safe_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in name)
        return safe_name.lower()
    
    def _build_filter_url(self, page: int = 1) -> str:
        """
        Build URL with optional filters.
        
        Args:
            page: Page number
            
        Returns:
            URL string with filters applied
        """
        base_url = self.SPELLS_URL
        params = []
        
        if page > 1:
            params.append(f"page={page}")
        
        # Add source filter using numeric ID
        if self.source_filter:
            source_data = self.SOURCE_FILTERS.get(self.source_filter.lower())
            if source_data:
                source_id = source_data[0]  # Extract numeric ID
                params.append(f"filter-source={source_id}")
            else:
                logger.warning(f"Unknown source filter: {self.source_filter}")
        
        if params:
            return f"{base_url}?{'&'.join(params)}"
        return base_url
    
    def _is_spell_accessible(self, spell_html: str) -> bool:
        """
        Check if a spell is accessible by looking for the spell-source element.
        
        Args:
            spell_html: HTML content of spell page
            
        Returns:
            True if spell has a spell-source element, False otherwise
        """
        soup = BeautifulSoup(spell_html, 'html.parser')
        source_elem = soup.find('p', class_='spell-source')
        return source_elem is not None
    
    def _should_include_spell(self, spell_html: str) -> bool:
        """
        Check if a spell should be included based on source filter.
        
        Args:
            spell_html: HTML content of spell page
            
        Returns:
            True if spell should be included
        """
        if not self.source_filter:
            return True
        
        # Get the friendly name for the source filter
        source_data = self.SOURCE_FILTERS.get(self.source_filter.lower())
        if not source_data:
            logger.warning(f"Unknown source filter: {self.source_filter}")
            return False
        
        source_name = source_data[1]  # Extract friendly name
        
        # Parse HTML and look specifically at the spell-source tag
        soup = BeautifulSoup(spell_html, 'html.parser')
        source_elem = soup.find('p', class_='spell-source')
        
        if not source_elem:
            logger.warning("Could not find spell-source tag in HTML")
            return False
        
        source_text = source_elem.get_text().strip()
        
        # Check if the source filter matches the actual source
        return source_name.lower() in source_text.lower()
    
    def get_spell_links(self) -> List[str]:
        """
        Extract all spell links from the main spells page.
        
        Note: This gets the first page. D&D Beyond uses pagination,
        so you may need to handle multiple pages or use their API.
        
        Returns:
            List of spell URLs
        """
        if self.source_filter:
            source_data = self.SOURCE_FILTERS.get(self.source_filter.lower())
            if source_data:
                source_name = source_data[1]  # Extract friendly name
                logger.info(f"Fetching spell list (filtering by source: {source_name})...")
            else:
                logger.warning(f"Unknown source filter: {self.source_filter}")
                logger.info("Fetching spell list from main page...")
        else:
            logger.info("Fetching spell list from main page...")
        
        spell_links = []
        page = 1
        
        while True:
            # Build URL with filters
            url = self._build_filter_url(page)
            
            try:
                response = self._get_page(url)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find spell links - adjust selector based on page structure
                # This is a basic selector and may need adjustment
                links = soup.select('a[href*="/spells/"]')
                
                if not links:
                    logger.info(f"No more spells found on page {page}")
                    break
                
                page_spell_links = []
                for link in links:
                    href = link.get('href')
                    if href and '/spells/' in href:
                        full_url = urljoin(self.BASE_URL, href)
                        # Filter out list page itself
                        if full_url != self.SPELLS_URL and full_url not in page_spell_links:
                            page_spell_links.append(full_url)
                
                unique_new = [url for url in page_spell_links if url not in spell_links]
                spell_links.extend(unique_new)
                
                logger.info(f"Page {page}: Found {len(unique_new)} new spell links (total: {len(spell_links)})")
                
                # Check if there's a next page button
                next_button = soup.select_one('a[href*="page="]')
                if not next_button or page > 50:  # Safety limit
                    break
                    
                page += 1
                
            except Exception as e:
                logger.error(f"Error fetching page {page}: {e}")
                break
        
        # Remove duplicates while preserving order
        unique_links = []
        seen = set()
        for link in spell_links:
            if link not in seen:
                seen.add(link)
                unique_links.append(link)
        
        logger.info(f"Total unique spell links found: {len(unique_links)}")
        return unique_links
    
    def download_spell(self, url: str) -> bool:
        """
        Download a single spell page.
        
        Args:
            url: URL of the spell page
            
        Returns:
            True if successful, False otherwise
        """
        if url in self.downloaded_urls:
            logger.info(f"Already downloaded: {url}")
            return True
        
        if url in self.skipped_urls:
            logger.info(f"Previously skipped (wrong source): {url}")
            return False
        
        try:
            # Extract spell name from URL
            spell_slug = url.split('/spells/')[-1].split('?')[0]
            filename = self._sanitize_filename(spell_slug) + '.html'
            filepath = self.output_dir / filename
            other_filepath = self.other_sources_dir / filename if self.other_sources_dir else None
            unaccessible_filepath = self.unaccessible_dir / filename
            
            # Check if file already exists in any directory
            if filepath.exists():
                logger.info(f"File already exists, skipping: {filepath.name}")
                # Mark as downloaded in progress tracker
                self.downloaded_urls.add(url)
                self._save_progress()
                return True
            
            if other_filepath and other_filepath.exists():
                logger.info(f"File already exists in other sources, skipping: {other_filepath.name}")
                # Mark as downloaded in progress tracker
                self.downloaded_urls.add(url)
                self._save_progress()
                return True
            
            if unaccessible_filepath.exists():
                logger.info(f"File already exists in unaccessible, skipping: {unaccessible_filepath.name}")
                # Mark as downloaded in progress tracker
                self.downloaded_urls.add(url)
                self._save_progress()
                return True
            
            logger.info(f"Downloading: {url}")
            response = self._get_page(url)
            
            # Check if spell is accessible (has spell-source element)
            if not self._is_spell_accessible(response.text):
                # Save to unaccessible directory
                with open(unaccessible_filepath, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                logger.info(f"Saved to unaccessible (no spell-source): {unaccessible_filepath}")
                # Mark as downloaded
                self.downloaded_urls.add(url)
                self._save_progress()
                return True
            
            # Apply source filter if specified
            if self.source_filter and not self._should_include_spell(response.text):
                # Save to other sources directory instead of skipping
                if self.other_sources_dir:
                    with open(other_filepath, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    logger.info(f"Saved to other sources: {other_filepath}")
                else:
                    # If no other_sources_dir, track as skipped (shouldn't happen)
                    source_data = self.SOURCE_FILTERS.get(self.source_filter.lower())
                    source_name = source_data[1] if source_data else self.source_filter
                    logger.info(f"Skipping (not from {source_name}): {url}")
                    self.skipped_urls.add(url)
                    self._save_progress()
                    return False
            else:
                # Save HTML to main directory
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                logger.info(f"Saved: {filepath}")
            
            # Mark as downloaded
            self.downloaded_urls.add(url)
            self._save_progress()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            return False
    
    def crawl(self, max_spells: int = None):
        """
        Main crawl method - downloads all spells.
        
        Args:
            max_spells: Maximum number of spells to download (None for all)
        """
        logger.info("Starting D&D Beyond spell crawler...")
        logger.info(f"Base directory: {self.base_dir.absolute()}")
        if self.source_filter:
            logger.info(f"  In-source spells → {self.output_dir.name}/")
            logger.info(f"  Other spells → {self.other_sources_dir.name}/")
        logger.info(f"  Inaccessible spells → {self.unaccessible_dir.name}/")
        logger.info(f"Rate limit delay: {self.delay} seconds")
        
        # Get all spell links (from cache or by crawling)
        if self.all_spell_urls:
            logger.info(f"Using {len(self.all_spell_urls)} cached spell URLs from progress file")
            spell_links = self.all_spell_urls
        else:
            logger.info("Discovering spell URLs...")
            spell_links = self.get_spell_links()
            
            if not spell_links:
                logger.warning("No spell links found! The page structure may have changed.")
                return
            
            # Save discovered URLs for future runs
            self.all_spell_urls = spell_links
            self._save_progress()
            logger.info(f"Saved {len(spell_links)} spell URLs to progress file")
        
        # Limit if requested
        if max_spells:
            spell_links = spell_links[:max_spells]
            logger.info(f"Limiting to {max_spells} spells")
        
        # Download each spell
        total = len(spell_links)
        successful = 0
        failed = 0
        
        for i, url in enumerate(spell_links, 1):
            logger.info(f"[{i}/{total}] Processing: {url}")
            
            if self.download_spell(url):
                successful += 1
            else:
                failed += 1
        
        logger.info("\n" + "="*50)
        logger.info("Crawl complete!")
        logger.info(f"Total spells processed: {total}")
        logger.info(f"Successfully downloaded: {successful}")
        logger.info(f"Failed: {failed}")
        
        # Count files in each directory
        unaccessible_count = len(list(self.unaccessible_dir.glob("*.html")))
        
        if self.source_filter:
            in_source_count = len(list(self.output_dir.glob("*.html")))
            not_in_source_count = len(list(self.other_sources_dir.glob("*.html")))
            logger.info(f"\nBase directory: {self.base_dir.absolute()}")
            logger.info(f"  {self.output_dir.name}/: {in_source_count} spells")
            logger.info(f"  {self.other_sources_dir.name}/: {not_in_source_count} spells")
            logger.info(f"  {self.unaccessible_dir.name}/: {unaccessible_count} spells")
        else:
            total_count = len(list(self.output_dir.glob("*.html")))
            logger.info(f"\nTotal spells saved: {total_count}")
            logger.info(f"  Location: {self.output_dir.absolute()}")
            logger.info(f"  {self.unaccessible_dir.name}/: {unaccessible_count} spells")
        
        if self.skipped_urls:
            logger.info(f"\nSkipped (failed to download): {len(self.skipped_urls)}")
        
        logger.info("="*50)


def parse_raw_cookies(cookie_string: str) -> dict:
    """
    Parse raw browser cookie string into a dictionary.
    
    Args:
        cookie_string: Cookie string in format "key1=value1; key2=value2"
        
    Returns:
        Dictionary of cookie key-value pairs
    """
    cookies = {}
    for item in cookie_string.split(';'):
        item = item.strip()
        if '=' in item:
            key, value = item.split('=', 1)
            cookies[key.strip()] = value.strip()
    return cookies


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Download D&D Beyond spell pages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download all spells with 2 second delay
  python spell_crawler.py
  
  # Download only 10 spells for testing
  python spell_crawler.py --max-spells 10
  
  # Download only Player's Handbook spells
  python spell_crawler.py --source phb
  
  # Download Xanathar's Guide spells
  python spell_crawler.py --source xge
  
  # Use custom output directory and faster rate
  python spell_crawler.py --output my_spells --delay 1.0
  
  # Use session cookies (raw browser format - easiest!)
  python spell_crawler.py --cookies-raw "CobaltSession=eyJ...; LoginState=c17..."
  
  # Use raw cookies from a file (good for long cookie strings)
  python spell_crawler.py --cookies-raw-file cookies.txt
  
  # Use session cookies (JSON format)
  python spell_crawler.py --cookies '{"CobaltSession": "your-session-cookie"}'
  
  # Use cookies from a JSON file
  python spell_crawler.py --cookies-file cookies.json
  
Source book codes (common):
  Core rulebooks:
    phb, players-handbook  - Player's Handbook (2014)
    phb-2024              - Player's Handbook (2024)
    dmg                   - Dungeon Master's Guide (2014)
    dmg-2024              - Dungeon Master's Guide (2024)
    mm, monster-manual    - Monster Manual (2014)
    mm-2024               - Monster Manual (2024)
    basic, basic-rules    - Basic Rules (2014)
    basic-2024            - D&D Beyond Basic Rules (2024)
  
  Popular expansions:
    xge, xanathars        - Xanathar's Guide to Everything
    tce, tashas           - Tasha's Cauldron of Everything
    ftod, fizbans         - Fizban's Treasury of Dragons
    scag                  - Sword Coast Adventurer's Guide
    eepc                  - Elemental Evil Player's Companion
    vgtm, volos           - Volo's Guide to Monsters
    mtof, mordenkainens   - Mordenkainen's Tome of Foes
    mpmm                  - Mordenkainen Presents: Monsters of the Multiverse
  
  Campaign settings:
    ggtr, ravnica         - Guildmasters' Guide to Ravnica
    egtw, wildemount      - Explorer's Guide to Wildemount
    mot, theros           - Mythic Odysseys of Theros
    erlw, eberron         - Eberron: Rising from the Last War
    scc, strixhaven       - Strixhaven: A Curriculum of Chaos
    vrgtr, ravenloft      - Van Richten's Guide to Ravenloft
  
  (See SOURCE_FILTERS in code for complete list including adventures)

Directory structure:
  Without --source filter:
    Accessible spells     → <output_dir>/
    Inaccessible spells   → <output_dir>/unaccessible/
  
  With --source filter (e.g., --source phb):
    Matching spells       → <output_dir>/in_source/
    Other spells          → <output_dir>/not_in_source/
    Inaccessible spells   → <output_dir>/unaccessible/
  
  Note: Inaccessible spells are those without a 'spell-source' element,
        typically indicating content you don't have access to.
  
IMPORTANT: Please respect D&D Beyond's Terms of Service.
This is for personal/educational use only.
        """
    )
    
    parser.add_argument(
        '--output', '-o',
        default='crawler/spell_pages',
        help='Output directory for HTML files (default: crawler/spell_pages)'
    )
    
    parser.add_argument(
        '--delay', '-d',
        type=float,
        default=2.0,
        help='Delay between requests in seconds (default: 2.0)'
    )
    
    parser.add_argument(
        '--max-spells', '-m',
        type=int,
        help='Maximum number of spells to download (default: all)'
    )
    
    parser.add_argument(
        '--source', '-s',
        type=str,
        help='Filter by source book (e.g., phb, xge, tce)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--cookies',
        type=str,
        help='Session cookies as JSON string (e.g., \'{"CobaltSession": "value"}\')'
    )
    
    parser.add_argument(
        '--cookies-raw',
        type=str,
        help='Session cookies in raw browser format (e.g., "cookie1=value1; cookie2=value2")'
    )
    
    parser.add_argument(
        '--cookies-file',
        type=str,
        help='Path to JSON file containing session cookies'
    )
    
    parser.add_argument(
        '--cookies-raw-file',
        type=str,
        help='Path to file containing raw browser format cookies'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Parse cookies if provided
    cookies = None
    if args.cookies:
        try:
            cookies = json.loads(args.cookies)
            logger.info(f"Loaded cookies from command line (JSON)")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse cookies JSON: {e}")
            return
    elif args.cookies_raw:
        try:
            cookies = parse_raw_cookies(args.cookies_raw)
            logger.info(f"Loaded {len(cookies)} cookies from raw format")
        except Exception as e:
            logger.error(f"Failed to parse raw cookies: {e}")
            return
    elif args.cookies_file:
        try:
            with open(args.cookies_file, 'r') as f:
                cookies = json.load(f)
            logger.info(f"Loaded cookies from file: {args.cookies_file}")
        except FileNotFoundError:
            logger.error(f"Cookies file not found: {args.cookies_file}")
            return
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse cookies file: {e}")
            return
    elif args.cookies_raw_file:
        try:
            with open(args.cookies_raw_file, 'r') as f:
                cookie_string = f.read().strip()
            cookies = parse_raw_cookies(cookie_string)
            logger.info(f"Loaded {len(cookies)} cookies from raw file: {args.cookies_raw_file}")
        except FileNotFoundError:
            logger.error(f"Cookies file not found: {args.cookies_raw_file}")
            return
        except Exception as e:
            logger.error(f"Failed to parse raw cookies file: {e}")
            return
    
    # Create crawler and run
    crawler = SpellCrawler(
        output_dir=args.output, 
        delay=args.delay,
        source_filter=args.source,
        cookies=cookies
    )
    crawler.crawl(max_spells=args.max_spells)


if __name__ == '__main__':
    main()
