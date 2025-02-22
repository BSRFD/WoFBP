import requests
import json
import sys
import datetime
import pytz
import os

API_URL = "https://www.wheeloffortune.com/api/bonus-puzzle-data"

def get_eastern_date():
    eastern = pytz.timezone('America/New_York')
    return datetime.datetime.now(eastern).date()

def parse_api_date(api_date_str):
    try:
        return datetime.datetime.strptime(api_date_str, '%b %d, %Y').date()
    except:
        return None

def main():
    manual_trigger = os.getenv("GITHUB_EVENT_NAME") == "workflow_dispatch"
    if manual_trigger:
        print("Bypassing time check for manual trigger")
    
    try:
        # Load existing data
        try:
            with open('data.json', 'r') as f:
                existing_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_data = {"date": "No data yet", "solution": "Check back later"}

        # Fetch API data
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        api_data = response.json()

        # Extract puzzle data
        puzzle_data = None
        for component in api_data.get('components', []):
            if component.get('componentName') == 'bonusPuzzle':
                puzzle_data = component.get('data', {})
                break

        if not puzzle_data:
            print("Error: Bonus puzzle component not found")
            sys.exit(1)

        # Process solution and date
        raw_solution = puzzle_data.get('solution', '')
        solution = ' '.join(
            part.strip() 
            for part in raw_solution.split('/') 
            if part.strip()
        ).upper()
        api_date_str = puzzle_data.get('date', '')
        api_date = parse_api_date(api_date_str)
        today_date = get_eastern_date()

        # Only validate dates for automated runs
        if not manual_trigger:
            if not api_date:
                print(f"Invalid API date format: {api_date_str}")
                sys.exit(1)
                
            if api_date != today_date:
                print(f"API date {api_date_str} not today's date")
                sys.exit(1)  # Non-zero for retry

        if api_date_str == existing_data.get('date'):
            print("Already has today's solution")
            sys.exit(0)

        # Archive previous solution
        if existing_data['date'] not in ["No data yet", ""]:
            past_file = 'past-solutions.json'
            past_data = []
            
            if os.path.exists(past_file):
                with open(past_file, 'r') as f:
                    past_data = json.load(f)
            
            past_data.append({
                "date": existing_data['date'],
                "solution": existing_data['solution']
            })
            past_data = past_data[-365:]
            
            with open(past_file, 'w') as f:
                json.dump(past_data, f)

        # Update with new solution
        with open('data.json', 'w') as f:
            json.dump({
                "date": api_date_str,
                "solution": solution
            }, f)

        print(f"Updated to {api_date_str}: {solution}")
        sys.exit(0)

    except Exception as e:
        print(f"ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
