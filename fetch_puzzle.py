import requests
import json
import sys
import datetime
import pytz

API_URL = "https://www.wheeloffortune.com/api/bonus-puzzle-data"

def is_already_updated():
    """Check if we've already updated today's puzzle"""
    try:
        with open('last_updated.txt', 'r') as f:
            last_date = f.read().strip()
        
        eastern = pytz.timezone('America/New_York')
        current_date = datetime.datetime.now(eastern).strftime('%Y-%m-%d')
        return last_date == current_date
        
    except FileNotFoundError:
        return False

def record_update():
    """Record today's date as last update"""
    eastern = pytz.timezone('America/New_York')
    current_date = datetime.datetime.now(eastern).strftime('%Y-%m-%d')
    with open('last_updated.txt', 'w') as f:
        f.write(current_date)

# ... (keep the existing find_bonus_puzzle_component function) ...

def main():
    if is_already_updated():
        print("Already updated today. Exiting.")
        return False

    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        api_data = response.json()

        puzzle_data = find_bonus_puzzle_component(api_data)
        if not puzzle_data:
            print("Error: Bonus puzzle data not found", file=sys.stderr)
            return False

        # ... (keep existing solution processing logic) ...

        if date != existing_data.get('date') or solution != existing_data.get('solution'):
            with open('data.json', 'w') as f:
                json.dump({"date": date, "solution": solution}, f)
            
            record_update()  # Add this line
            print(f"Updated: {date} - {solution}")
            return True

        print("No changes detected")
        return False

    # ... (keep existing error handling) ...
