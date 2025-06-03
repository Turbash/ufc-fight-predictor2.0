from collections import defaultdict
from . import data_manager

def update_fighter_index(all_fights_data):
    """
    Builds or updates the fighter index from all fights data.
    The index maps weight classes to a list of fighters (name, url).
    """
    print("Updating fighter index...")
    fighter_index = defaultdict(list)
    # Use a set to store (name, url, weight_class) tuples to ensure uniqueness per weight class
    unique_fighters_in_class = defaultdict(set)

    for fight in all_fights_data:
        wc = fight.get("weight_class", "Unknown")
        if wc == "N/A" or not wc: wc = "Unknown"

        fighters_in_fight = [
            {"name": fight.get("fighter1_name"), "url": fight.get("fighter1_url")},
            {"name": fight.get("fighter2_name"), "url": fight.get("fighter2_url")}
        ]

        for fighter in fighters_in_fight:
            if fighter["name"] and fighter["name"] != "N/A" and fighter["url"]:
                fighter_tuple = (fighter["name"], fighter["url"])
                # Add fighter to this weight class if not already present
                if fighter_tuple not in unique_fighters_in_class[wc]:
                    unique_fighters_in_class[wc].add(fighter_tuple)
                    fighter_index[wc].append({"name": fighter["name"], "url": fighter["url"]})
    
    # Sort fighters by name within each weight class
    for wc in fighter_index:
        fighter_index[wc] = sorted(fighter_index[wc], key=lambda x: x['name'])

    data_manager.save_fighter_index(dict(fighter_index)) # Convert defaultdict to dict for saving
    print("Fighter index updated.")
    return dict(fighter_index)

def get_weight_classes():
    """Returns a list of available weight classes from the fighter index."""
    fighter_index = data_manager.load_fighter_index()
    return sorted(list(fighter_index.keys()))

def get_fighters_by_weight_class(weight_class):
    """Returns a list of fighters for a given weight class."""
    fighter_index = data_manager.load_fighter_index()
    return fighter_index.get(weight_class, [])

