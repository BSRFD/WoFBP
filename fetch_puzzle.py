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

def should_run(manual_trigger: bool):
    if manual_trigger:
        print("Bypassing time check for manual trigger")
        return True
        
    eastern = pytz.timezone('America/New_York')
    now = datetime.datetime.now(eastern)
    return (
        now.weekday() < 5 and  # 0-4 = Mon-Fri
        datetime.time(16, 59) <= now.time() <= datetime.time(17, 3)
    )

def main():
    manual_trigger = os.getenv("GITHUB_EVENT_NAME") == "workflow_dispatch"
    
    if not should_run(manual_trigger):
        print("Outside scheduled monitoring window")
        sys.exit(0)

    try:
        # Load existing data
        try:
            with open('data.json', 'r') as f:
                existing_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_data = {"date": "", "solution": ""}

        # Fetch API data
        print(f"Fetching API data from {API_URL}")
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

        print(f"API Date: {api_date_str} | Today's Date: {today_date}")
        print(f"Existing Solution Date: {existing_data.get('date')}")

        # Only update if API date matches today
        if api_date != today_date:
            print("API date not today - skipping update")
            sys.exit(0)

        if api_date_str == existing_data.get('date'):
            print("Already has today's solution")
            sys.exit(0)

        # Update data.json
        with open('data.json', 'w') as f:
            json.dump({
                "date": api_date_str,
                "solution": solution
            }, f)

        print(f"Successfully updated to {api_date_str}: {solution}")
        sys.exit(0)

    except Exception as e:
        print(f"ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
