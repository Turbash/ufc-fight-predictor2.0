import re

def clean_text(text):
    """Cleans text by stripping whitespace and removing excessive newlines/spaces."""
    if text is None:
        return ""
    return ' '.join(text.split()).strip()

def parse_fighter_id_from_url(fighter_url):
    """Extracts fighter ID from their UFCStats profile URL."""
    if not fighter_url:
        return None
    match = re.search(r'fighter-details/([a-zA-Z0-9]+)$', fighter_url)
    return match.group(1) if match else None

def normalize_weight_class(wc_string):
    """Normalizes weight class strings like 'Flyweight Bout' to 'Flyweight'."""
    if wc_string is None:
        return "Unknown"
    wc_string = clean_text(wc_string)
    # Remove "Bout", "Title Bout", "Interim Title Bout", "Ultimate Fighter Tournament Final" etc.
    # Also handle "Women's" prefix and specific tournament names
    wc_string = re.sub(r'\s+(Bout|Title Bout|Interim.*Title Bout|Catch Weight.*|The Ultimate Fighter.*Final|Tournament.*Final)$', '', wc_string, flags=re.IGNORECASE)
    # Remove "UFC" prefix if present
    wc_string = re.sub(r'^UFC\s+', '', wc_string, flags=re.IGNORECASE)
    # Handle "Women's Strawweight" -> "Women's Strawweight" (no change needed here, but good to be aware)
    # Ensure "Women's" is kept if present, e.g. "Women's Strawweight"
    # The regex above should correctly keep "Women's Strawweight" as it doesn't match "Bout" etc. at the end of "Women's"
    
    # Specific known variations that need more direct handling if the regex isn't enough
    # For example, if "Catch Weight Bout" becomes "Catch Weight", we might want to normalize it further or leave as is.
    # Current regex handles "Catch Weight Bout" -> "Catch Weight"
    
    return clean_text(wc_string) if wc_string else "Unknown"

def parse_career_stat_value(stat_text):
    """Parses values like 'SLpM: 5.25' into '5.25' or '50%' into '50%'."""
    if ':' in stat_text:
        return clean_text(stat_text.split(':')[1])
    return clean_text(stat_text)

def parse_height_to_cm(height_str):
    """Converts height string 'X' Y"' to centimeters."""
    if not height_str or '--' in height_str:
        return None
    feet, inches = 0, 0
    # Remove spaces around ' and " for easier parsing
    height_str = height_str.replace(' ', '')
    parts = height_str.replace('"', '').split("'")
    try:
        if len(parts) == 2:
            feet = int(parts[0])
            if parts[1]: # Check if inches part is not empty
                inches = int(parts[1])
        elif len(parts) == 1 and parts[0]: # Only inches or error
            # This could be '71"' (becomes ['71']) or just '5' (becomes ['5'] from 5')
            if "'" in height_str and '"' not in height_str : # e.g. "5'"
                 feet = int(parts[0])
                 inches = 0
            elif '"' in height_str: # e.g. "71\""
                inches = int(parts[0])
            else: # malformed
                return None
        else: # Malformed or empty
            return None
    except ValueError:
        return None # Conversion to int failed
        
    total_inches = (feet * 12) + inches
    return round(total_inches * 2.54)

def parse_reach_to_cm(reach_str):
    """Converts reach string 'X"' to centimeters."""
    if not reach_str or '--' in reach_str:
        return None
    try:
        # Remove spaces and the quote
        reach_str = reach_str.replace(' ', '').replace('"', '')
        inches = float(reach_str)
        return round(inches * 2.54)
    except ValueError:
        return None

def parse_weight_to_lbs(weight_str):
    """Converts weight string 'X lbs.' to pounds (numeric)."""
    if not weight_str or '--' in weight_str:
        return None
    try:
        # Remove " lbs." and any spaces
        weight_str = weight_str.replace(' lbs.', '').replace(' ', '')
        return float(weight_str)
    except ValueError:
        return None
