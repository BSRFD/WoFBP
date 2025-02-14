import requests
import json
import sys
import datetime
import pytz
import os  # Added

API_URL = "https://www.wheeloffortune.com/api/bonus-puzzle-data"

# ... (existing functions remain the same until main() ... 

def main():
    if not should_run(manual_trigger):
        print(f"Outside monitoring window (manual_trigger={manual_trigger})")
        sys.exit(0)

    try:
        # ... (existing data loading and API call logic) ...

        if api_date_str == existing_data.get('date'):
            print("Already has today's solution")
            sys.exit(0)

        # Update data.json
        with open('data.json', 'w') as f:
            json.dump({"date": api_date_str, "solution": solution}, f)

        # NEW: Update past solutions
        past_file = 'past-solutions.json'
        past_data = []
        if os.path.exists(past_file):
            with open(past_file, 'r') as f:
                past_data = json.load(f)
        
        # Add new entry if not exists
        if not any(entry['date'] == api_date_str for entry in past_data):
            past_data.append({
                "date": api_date_str,
                "solution": solution
            })
            # Keep last 30 entries
            past_data = past_data[-30:]
            with open(past_file, 'w') as f:
                json.dump(past_data, f)

        print(f"Successfully updated to {api_date_str}: {solution}")
        sys.exit(0)

    # ... (rest of existing code remains the same) ...
