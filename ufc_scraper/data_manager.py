import json
import os
from . import config
from . import utils # For parse_fighter_id_from_url
from datetime import datetime

def save_json(data, filepath):
    """Saves data to a JSON file."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"Data saved to {filepath}")
    except IOError as e:
        print(f"Error saving data to {filepath}: {e}")

def load_json(filepath):
    """Loads data from a JSON file."""
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error loading data from {filepath}: {e}")
        return None

# Event Data
def save_events_data(events):
    save_json(events, config.EVENTS_FILE)

def load_events_data():
    return load_json(config.EVENTS_FILE) or []

# Fights Data
def save_fights_data(fights):
    save_json(fights, config.FIGHTS_FILE)

def load_fights_data():
    return load_json(config.FIGHTS_FILE) or []

# Fighter Index
def save_fighter_index(index):
    save_json(index, config.FIGHTER_INDEX_FILE)

def load_fighter_index():
    return load_json(config.FIGHTER_INDEX_FILE) or {}

# Individual Fighter Profiles
def save_fighter_profile_data(fighter_data):
    fighter_id = utils.parse_fighter_id_from_url(fighter_data.get("url"))
    if not fighter_id:
        print(f"Could not save fighter profile, missing ID: {fighter_data.get('name')}")
        return
    
    fighter_data["last_scraped_timestamp"] = datetime.now().isoformat()
    filepath = config.FIGHTER_PROFILES_DIR / f"{fighter_id}.json"
    save_json(fighter_data, filepath)

def load_fighter_profile_data(fighter_url):
    fighter_id = utils.parse_fighter_id_from_url(fighter_url)
    if not fighter_id:
        return None
    
    filepath = config.FIGHTER_PROFILES_DIR / f"{fighter_id}.json"
    return load_json(filepath)

def get_fighter_last_fight_date(fighter_url, all_fights_data):
    """Gets the most recent fight date for a fighter from all_fights_data."""
    latest_date = None
    fighter_id = utils.parse_fighter_id_from_url(fighter_url) # Ensure we compare IDs if names are ambiguous
    
    for fight in all_fights_data:
        fight_date_str = fight.get("event_date") # Assuming event_date is stored with fights
        if not fight_date_str:
            continue

        is_participant = False
        if fighter_url == fight.get("fighter1_url") or fighter_url == fight.get("fighter2_url"):
            is_participant = True
        
        if is_participant:
            try:
                current_fight_date = datetime.strptime(fight_date_str, "%B %d, %Y")
                if latest_date is None or current_fight_date > latest_date:
                    latest_date = current_fight_date
            except ValueError:
                # Handle cases where date format might be different or invalid
                print(f"Warning: Could not parse date '{fight_date_str}' for fight involving {fighter_url}")
                continue
                
    return latest_date.strftime("%Y-%m-%d") if latest_date else None
