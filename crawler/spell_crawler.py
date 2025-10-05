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
    
    # Source book filter mapping (common sources)
    SOURCE_FILTERS = {
        'phb': 'Player’s Handbook',
        'players-handbook': 'Player\'s Handbook',
        'xge': 'Xanathar\'s Guide to Everything',
        'xanathars': 'Xanathar\'s Guide to Everything',
        'tce': 'Tasha\'s Cauldron of Everything',
        'tashas': 'Tasha\'s Cauldron of Everything',
        'scag': 'Sword Coast Adventurer\'s Guide',
        'eepc': 'Elemental Evil Player\'s Companion',
        'ftod': 'Fizban\'s Treasury of Dragons',
        'fizbans': 'Fizban\'s Treasury of Dragons',
        'basic': 'Basic Rules',
        'basic-rules': 'Basic Rules',
        'dmg': 'Dungeon Master\'s Guide',
        'explorers-guide': 'Explorer\'s Guide to Wildemount',
        'ggtr': 'Guildmasters\' Guide to Ravnica',
        'ai': 'Acquisitions Incorporated',
    }
    
    def __init__(self, output_dir: str = "spell_pages", delay: float = 1.0, 
                 source_filter: str = None):
        """
        Initialize the crawler.
        
        Args:
            output_dir: Directory to save HTML files
            delay: Delay between requests in seconds (be respectful!)
            source_filter: Optional source book filter (e.g., 'phb', 'xge', 'tce')
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.delay = delay
        self.source_filter = source_filter
        
        # Track progress
        self.progress_file = self.output_dir / "progress.json"
        self.downloaded_urls, self.skipped_urls = self._load_progress()
        
        # Session with headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
    
    def _load_progress(self) -> tuple[Set[str], Set[str]]:
        """Load previously downloaded and skipped URLs from progress file."""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r') as f:
                    data = json.load(f)
                    downloaded = set(data.get('downloaded', []))
                    skipped = set(data.get('skipped', []))
                    return downloaded, skipped
            except Exception as e:
                logger.warning(f"Could not load progress file: {e}")
        return set(), set()
    
    def _save_progress(self):
        """Save progress to file."""
        try:
            with open(self.progress_file, 'w') as f:
                json.dump({
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
        
        # Note: D&D Beyond's actual filter parameters may differ
        # The site likely uses POST requests or JavaScript for filtering
        # This is a basic implementation that may need adjustment
        if self.source_filter:
            # Try to add source filter (actual parameter name may vary)
            params.append(f"filter-source={self.source_filter}")
        
        if params:
            return f"{base_url}?{'&'.join(params)}"
        return base_url
    
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
        source_name = self.SOURCE_FILTERS.get(self.source_filter.lower(), self.source_filter)
        
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
            source_name = self.SOURCE_FILTERS.get(self.source_filter.lower(), self.source_filter)
            logger.info(f"Fetching spell list (filtering by source: {source_name})...")
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
            
            # Check if file already exists on disk
            if filepath.exists():
                logger.info(f"File already exists, skipping: {filepath.name}")
                # Mark as downloaded in progress tracker
                self.downloaded_urls.add(url)
                self._save_progress()
                return True
            
            logger.info(f"Downloading: {url}")
            response = self._get_page(url)
            
            # Apply source filter if specified
            if self.source_filter and not self._should_include_spell(response.text):
                source_name = self.SOURCE_FILTERS.get(self.source_filter.lower(), self.source_filter)
                logger.info(f"Skipping (not from {source_name}): {url}")
                # Track as skipped so we don't check again
                self.skipped_urls.add(url)
                self._save_progress()
                return False
            
            # Save HTML
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            # Mark as downloaded
            self.downloaded_urls.add(url)
            self._save_progress()
            
            logger.info(f"Saved: {filepath}")
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
        logger.info(f"Output directory: {self.output_dir.absolute()}")
        logger.info(f"Rate limit delay: {self.delay} seconds")
        
        # Get all spell links
        spell_links = self.get_spell_links()
        
        if not spell_links:
            logger.warning("No spell links found! The page structure may have changed.")
            return
        
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
        logger.info(f"Total spells: {total}")
        logger.info(f"Successfully downloaded: {successful}")
        logger.info(f"Failed: {failed}")
        if self.source_filter:
            logger.info(f"Skipped (wrong source): {len(self.skipped_urls)}")
        logger.info(f"Output directory: {self.output_dir.absolute()}")
        logger.info("="*50)


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
  
Source book codes:
  phb, players-handbook    - Player's Handbook
  xge, xanathars          - Xanathar's Guide to Everything
  tce, tashas             - Tasha's Cauldron of Everything
  scag                    - Sword Coast Adventurer's Guide
  eepc                    - Elemental Evil Player's Companion
  ftod, fizbans           - Fizban's Treasury of Dragons
  basic, basic-rules      - Basic Rules
  dmg                     - Dungeon Master's Guide
  (See SOURCE_FILTERS in code for full list)
  
IMPORTANT: Please respect D&D Beyond's Terms of Service.
This is for personal/educational use only.
        """
    )
    
    parser.add_argument(
        '--output', '-o',
        default='spell_pages',
        help='Output directory for HTML files (default: spell_pages)'
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
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create crawler and run
    crawler = SpellCrawler(
        output_dir=args.output, 
        delay=args.delay,
        source_filter=args.source
    )
    crawler.crawl(max_spells=args.max_spells)


if __name__ == '__main__':
    main()
