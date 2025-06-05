import requests
from bs4 import BeautifulSoup
import time
from . import config
from . import utils

def get_soup(url):
    """Fetches content from URL and returns a BeautifulSoup object."""
    try:
        response = requests.get(url, headers=config.HEADERS)
        response.raise_for_status()  # Raise an exception for HTTP errors
        time.sleep(config.REQUEST_DELAY) # Respectful delay
        return BeautifulSoup(response.content, "lxml")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def scrape_event_list():
    """Scrapes the list of all completed UFC events."""
    print("Scraping event list...")
    soup = get_soup(config.BASE_URL)
    if not soup:
        return []

    events = []
    # Inspired by working event_scraper.py: Use simpler row selector
    table_rows = soup.select("tr.b-statistics__table-row")

    for row in table_rows:
        # These selectors target elements within the row.
        # The first td usually contains the event link and date.
        # The second td usually contains the location.
        event_link_tag = row.select_one("td:nth-child(1) a.b-link_style_black") # More direct selector for link in first td
        date_tag = row.select_one("td:nth-child(1) span.b-statistics__date")    # More direct selector for date in first td
        location_tag_td = row.select_one("td:nth-child(2)") # Location is typically in the second td

        if event_link_tag and date_tag: # Location is optional for an event to be valid
            event_name = utils.clean_text(event_link_tag.get_text())
            event_url = event_link_tag.get('href')
            event_date = utils.clean_text(date_tag.get_text())
            location = utils.clean_text(location_tag_td.get_text()) if location_tag_td else "N/A"
            
            if event_url: # Ensure event_url is not None
                full_event_url = config.FIGHTER_STATS_BASE_URL + event_url if not event_url.startswith('http') else event_url
            else:
                print(f"Warning: Found event '{event_name}' without a URL. Skipping.")
                continue

            events.append({
                "name": event_name,
                "date": event_date,
                "location": location,
                "url": full_event_url
            })
    print(f"Found {len(events)} events.")
    return events

def scrape_event_fights(event_url, event_date): # Added event_date parameter
    """Scrapes all fights from a given event URL."""
    print(f"Scraping fights for event: {event_url}")
    soup = get_soup(event_url)
    if not soup:
        return []

    fights = []
    # Inspired by working fight_scraper.py: Use row selector with 'data-link' attribute
    fight_rows = soup.select("tr.b-fight-details__table-row[data-link]")

    for row in fight_rows:
        # data-link attribute is already confirmed by the selector,
        # but keeping the .get('data-link') check is harmless.
        if row.get('data-link'): 
            cols = row.find_all("td", recursive=False)
            if len(cols) < 10: # Expect at least 10 columns for a fight row based on site structure
                continue

            # Fighter names and links from cols[1]
            # Inspired by working fight_scraper.py for robustness
            fighter_a_tags = cols[1].select("a")
            fighter1_tag = fighter_a_tags[0] if len(fighter_a_tags) > 0 else None
            fighter2_tag = fighter_a_tags[1] if len(fighter_a_tags) > 1 else None
            
            fighter1_name = utils.clean_text(fighter1_tag.get_text()) if fighter1_tag else "N/A"
            fighter1_href = fighter1_tag.get('href') if fighter1_tag else None
            fighter1_url = (config.FIGHTER_STATS_BASE_URL + fighter1_href) if fighter1_href and not fighter1_href.startswith('http') else fighter1_href
            
            fighter2_name = utils.clean_text(fighter2_tag.get_text()) if fighter2_tag else "N/A"
            fighter2_href = fighter2_tag.get('href') if fighter2_tag else None
            fighter2_url = (config.FIGHTER_STATS_BASE_URL + fighter2_href) if fighter2_href and not fighter2_href.startswith('http') else fighter2_href

            # Winner determination based on CSS classes of the status icon for fighter 1
            fighter1_status_tag = cols[0].select_one("p:nth-of-type(1) i.b-fight-details__person-status")
            winner = "N/A" # Default winner

            if fighter1_status_tag:
                status_classes = fighter1_status_tag.get('class', [])
                
                if 'b-fight-details__person-status_style_green' in status_classes: # Fighter 1 wins
                    winner = fighter1_name
                elif 'b-fight-details__person-status_style_red' in status_classes: # Fighter 1 loses (so Fighter 2 wins)
                    winner = fighter2_name
                elif 'b-fight-details__person-status_style_blue' in status_classes: # Draw
                    winner = "Draw"
                elif 'b-fight-details__person-status_style_yellow' in status_classes: # No Contest
                    winner = "No Contest"
                # If fighter_name itself is "N/A", winner will correctly be "N/A" (or "Draw"/"No Contest")

            # Fight details - Corrected column indices based on typical ufcstats.com structure
            # Weight class: cols[6]
            # Method: cols[7]
            # Round: cols[8]
            # Time: cols[9]
            
            weight_class_tag = cols[6].select_one("p.b-fight-details__table-text")
            weight_class_str = utils.clean_text(weight_class_tag.get_text()) if weight_class_tag else "Unknown"
            normalized_wc = utils.normalize_weight_class(weight_class_str)

            method_text = utils.clean_text(cols[7].get_text(separator=" ", strip=True)) # Method and details
            round_val = utils.clean_text(cols[8].get_text())
            time_val = utils.clean_text(cols[9].get_text())
            
            fight_details_href = row['data-link']
            full_fight_details_url = (config.FIGHTER_STATS_BASE_URL + fight_details_href) if fight_details_href and not fight_details_href.startswith('http') else fight_details_href


            fights.append({
                "fighter1_name": fighter1_name,
                "fighter1_url": fighter1_url,
                "fighter2_name": fighter2_name,
                "fighter2_url": fighter2_url,
                "winner": winner, # Winner is now determined by the logic above
                "method": method_text,
                "round": round_val,
                "time": time_val,
                "weight_class": normalized_wc,
                "fight_details_url": full_fight_details_url,
                "event_date": event_date # Added event_date
            })
    print(f"Found {len(fights)} fights for this event.")
    return fights

def scrape_fighter_profile(fighter_url):
    """Scrapes detailed statistics for a given fighter URL."""
    print(f"Scraping profile for fighter: {fighter_url}")
    soup = get_soup(fighter_url)
    if not soup:
        return None

    fighter_stats = {"url": fighter_url}
    
    # Name
    name_tag = soup.select_one("span.b-content__title-highlight")
    fighter_stats["name"] = utils.clean_text(name_tag.get_text()) if name_tag else "N/A"

    # Record
    record_tag = soup.select_one("span.b-content__title-record")
    fighter_stats["record"] = utils.clean_text(record_tag.get_text().replace("Record: ", "")) if record_tag else "N/A"

    # General Info (Height, Weight, Reach, Stance, DOB)
    info_list_items = soup.select("div.b-list__info-box_style_small-width ul.b-list__box-list li.b-list__box-list-item")
    for item in info_list_items:
        text_content = utils.clean_text(item.get_text(separator=": ", strip=True))
        if ":" in text_content:
            key, value = [utils.clean_text(part) for part in text_content.split(":", 1)]
            if key == "Height":
                fighter_stats["height_str"] = value
                fighter_stats["height_cm"] = utils.parse_height_to_cm(value)
            elif key == "Weight":
                fighter_stats["weight_str"] = value
                fighter_stats["weight_lbs"] = utils.parse_weight_to_lbs(value)
            elif key == "Reach":
                fighter_stats["reach_str"] = value
                fighter_stats["reach_cm"] = utils.parse_reach_to_cm(value)
            elif key == "STANCE": # Note: Key is STANCE on the site
                fighter_stats["stance"] = value
            elif key == "DOB":
                fighter_stats["dob"] = value
    
    # Career Statistics
    # Find the career stats box specifically
    career_stats_box = None
    all_info_boxes = soup.select("div.b-list__info-box")
    for box in all_info_boxes:
        title_tag = box.select_one("h3.b-list__info-box-title")
        if title_tag and "Career Statistics" in title_tag.get_text():
            career_stats_box = box
            break

    if career_stats_box:
        stat_items = career_stats_box.select("ul.b-list__box-list li.b-list__box-list-item")
        career_stats_map = {
            "SLpM": "slpm", "Str. Acc.": "str_acc", "SApM": "sapm", "Str. Def": "str_def", # Note: Str. Def might not have trailing period
            "TD Avg.": "td_avg", "TD Acc.": "td_acc", "TD Def.": "td_def", "Sub. Avg.": "sub_avg"
        }
        for item in stat_items:
            item_text = item.get_text(separator=": ", strip=True)
            if ":" in item_text:
                label, value = [utils.clean_text(part) for part in item_text.split(":", 1)]
                # Handle cases like "Str. Def." vs "Str. Def"
                normalized_label = label.replace('.', '') 
                for map_key, stat_name in career_stats_map.items():
                    if normalized_label == map_key.replace('.', ''):
                        fighter_stats[stat_name] = value
                        break
    
    # Extract last fight date from fight history table (most recent one)
    # This is a simplified approach; a more robust one would parse all fights
    # and find the latest date. For now, we'll rely on all_fights.json for this.
    # fighter_stats["last_fight_date_from_profile"] = "YYYY-MM-DD" # Placeholder

    print(f"Finished scraping profile for {fighter_stats.get('name', 'Unknown Fighter')}.")
    return fighter_stats

