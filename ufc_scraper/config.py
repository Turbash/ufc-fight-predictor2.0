import pathlib

BASE_URL = "http://ufcstats.com/statistics/events/completed?page=all"
FIGHTER_STATS_BASE_URL = "http://ufcstats.com" # Base for fighter and event detail links

# Project root directory
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent # This should be d:\temp\ufc-scraper

# Data storage paths
DATA_DIR = PROJECT_ROOT / "data"
EVENTS_FILE = DATA_DIR / "events.json"
FIGHTS_FILE = DATA_DIR / "all_fights.json"
FIGHTER_INDEX_FILE = DATA_DIR / "fighter_index.json"
FIGHTER_PROFILES_DIR = DATA_DIR / "fighter_profiles"

# Path to the large dataset CSV for model training
LARGE_DATASET_CSV = PROJECT_ROOT / "large_dataset.csv"

# Models directory
MODELS_DIR = PROJECT_ROOT / "models"

# Create data and models directories if they don't exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
FIGHTER_PROFILES_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Scraping delay in seconds to be respectful to the server
REQUEST_DELAY = 2 # seconds

# User agent for requests
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
HEADERS = {"User-Agent": USER_AGENT}
