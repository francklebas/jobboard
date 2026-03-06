import sys
import os

# Add parent directory to path so we can import from api modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scraper import run_scrape

if __name__ == "__main__":
    run_scrape()
