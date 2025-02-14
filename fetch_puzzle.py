import requests
import json
import sys
import datetime
import pytz

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
    try:
        # First check if we should even run
        eastern = pytz.timezone('America/New_York')
        now = datetime.datetime.now(eastern)
        
        # Only run Mon-Fri between 4:50 PM and 5:20 PM ET
        if now.weekday() >= 5 or not (datetime.time(16, 50) <= now.time() <= datetime.time(17, 20)):
            print("Outside monitoring window")
            sys.exit(0)

        # Load existing data
        try:
            with open('data.json', 'r') as f:
                existing_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_data = {"date": "", "solution": ""}

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
            print("Puzzle data not found in API response")
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
        
        # Get today's Eastern Time date
        today_date = get_eastern_date()

        # Only update if API date matches today
        if api_date != today_date:
            print(f"API date {api_date_str} not today's date")
            sys.exit(0)  # Not an error, just not updated yet

        if api_date_str == existing_data.get('date'):
            print("Already have today's solution")
            sys.exit(0)  # Success exit code

        # Update data.json
        with open('data.json', 'w') as f:
            json.dump({
                "date": api_date_str,
                "solution": solution
            }, f)

        print(f"Updated {api_date_str}: {solution}")
        sys.exit(0)

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
