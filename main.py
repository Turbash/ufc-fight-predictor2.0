from ufc_scraper import scraper, data_manager, fighter_organizer, config
import time

def main():
    # 1. Scrape all events
    print("Starting UFC Stats Scraper...")
    
    # Ensure data directories exist (though config.py should handle this)
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    config.FIGHTER_PROFILES_DIR.mkdir(parents=True, exist_ok=True)

    events = scraper.scrape_event_list()
    if not events:
        print("No events found or error scraping events. Exiting.")
        return
    data_manager.save_events_data(events)
    print(f"Successfully scraped and saved {len(events)} events.")

    # 2. Scrape fights for each event
    all_fights = []
    
    # Optional: Limit number of events to scrape for testing
    # events_to_scrape = events[:3] 
    events_to_scrape = events 

    for i, event in enumerate(events_to_scrape):
        print(f"Scraping event {i+1}/{len(events_to_scrape)}: {event['name']} ({event.get('date', 'N/A')})")
        # Pass event_date to scrape_event_fights; event['date'] is already in correct format from scrape_event_list
        fights_in_event = scraper.scrape_event_fights(event['url'], event['date'])
        
        for fight in fights_in_event:
            fight['event_name'] = event['name'] # Add event name for context
            # fight['event_date'] is added inside scrape_event_fights
        all_fights.extend(fights_in_event)
        
        # Respectful delay between scraping different event pages
        if i < len(events_to_scrape) - 1: # Don't sleep after the last event
            print(f"Waiting for {config.REQUEST_DELAY} seconds before next event...")
            time.sleep(config.REQUEST_DELAY) 
    
    if not all_fights:
        print("No fights were scraped. Check event details or network connectivity.")
    else:
        data_manager.save_fights_data(all_fights)
        print(f"Successfully scraped and saved {len(all_fights)} fights in total.")

    # 3. Update fighter index
    # Load all fights (either newly scraped or from file if scraping fights failed but we want to run index)
    current_fights_for_index = all_fights
    if not current_fights_for_index: 
        print("No new fights scraped from this run. Attempting to load existing fights for index update.")
        current_fights_for_index = data_manager.load_fights_data()
        if not current_fights_for_index:
            print("No fights data available (neither newly scraped nor existing). Cannot update fighter index.")
        else:
            print(f"Loaded {len(current_fights_for_index)} existing fights for index update.")
            fighter_organizer.update_fighter_index(current_fights_for_index)
    elif current_fights_for_index: # if all_fights has content
        fighter_organizer.update_fighter_index(current_fights_for_index)
    
    print("Fighter index processing completed.")

    # Optional: Scrape fighter profiles. This can take a very long time.
    # Consider running this as a separate, targeted script or on a schedule.
    # print("\nStarting fighter profile scraping (this might take a very long time)...")
    # fighter_index = data_manager.load_fighter_index()
    # if not fighter_index:
    #     print("Fighter index is empty. Cannot scrape profiles.")
    # else:
    #     all_unique_fighter_urls = set()
    #     for wc_fighters in fighter_index.values():
    #         for fighter in wc_fighters:
    #             if fighter.get('url'):
    #                 all_unique_fighter_urls.add(fighter['url'])
        
    #     print(f"Found {len(all_unique_fighter_urls)} unique fighter profiles to potentially scrape.")
    #     scraped_profiles_count = 0
    #     for i, fighter_url in enumerate(list(all_unique_fighter_urls)):
    #         # Basic check if profile already exists and is recent (optional, more complex logic needed for smart updates)
    #         # existing_profile = data_manager.load_fighter_profile_data(fighter_url)
    #         # if existing_profile and 'last_scraped_timestamp' in existing_profile:
    #         #     print(f"Profile for {fighter_url} already scraped. Skipping.")
    #         #     continue

    #         print(f"Scraping profile {i+1}/{len(all_unique_fighter_urls)}: {fighter_url}")
    #         profile_data = scraper.scrape_fighter_profile(fighter_url)
    #         if profile_data:
    #             data_manager.save_fighter_profile_data(profile_data)
    #             scraped_profiles_count +=1
    #         # Respectful delay between profile scrapes
    #         if i < len(all_unique_fighter_urls) - 1:
    #             time.sleep(config.REQUEST_DELAY) 
    #     print(f"Scraped {scraped_profiles_count} new fighter profiles.")

    print("\nUFC Scraping process completed.")

if __name__ == "__main__":
    main()
