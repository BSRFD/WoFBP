import requests
import json
import sys
import os
import pytz
from datetime import datetime

API_URL = "https://www.wheeloffortune.com/api/bonus-puzzle-data"
DATA_FILE = "data.json"
HISTORY_FILE = "past-solutions.json"
ET = pytz.timezone('America/New_York')

def get_current_date():
    """Get current ET date in YYYY-MM-DD format"""
    return datetime.now(ET).strftime('%Y-%m-%d')

def get_current_data():
    """Get stored solution and date from data.json"""
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            return {
                'solution': data.get('solution', ''),
                'date': data.get('date', '')
            }
    except (FileNotFoundError, json.JSONDecodeError):
        return {'solution': '', 'date': ''}

def fetch_api_data():
    """Fetch and parse API data"""
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        for component in data.get('components', []):
            if component.get('componentName') == 'bonusPuzzle':
                puzzle_data = component.get('data', {})
                return {
                    'solution': parse_solution(puzzle_data.get('solution', '')),
                    'date': puzzle_data.get('date', '')
                }
        raise ValueError("Bonus puzzle data not found")
    
    except Exception as e:
        print(f"API Error: {str(e)}")
        sys.exit(2)

def parse_solution(raw_solution):
    """Format solution string"""
    return ' '.join(
        part.strip().upper()
        for part in raw_solution.split('/')
        if part.strip()
    )

def archive_current_solution(current_solution, current_date):
    """Archive previous solutions"""
    try:
        if not current_solution:
            return

        history = []
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                history = json.load(f)
        
        # Add entry only if date not already archived
        if not any(entry['date'] == current_date for entry in history):
            history.append({
                "date": current_date,
                "solution": current_solution
            })
            # Keep max 1 year of history
            history = history[-365:]
            
            with open(HISTORY_FILE, 'w') as f:
                json.dump(history, f, indent=2)
                
    except Exception as e:
        print(f"Archive Error: {str(e)}")
        sys.exit(2)

def main():
    try:
        # Get current ET date
        today = get_current_date()
        
        # Get stored data
        stored_data = get_current_data()
        stored_date = stored_data['date']
        stored_solution = stored_data['solution']
        
        # Fetch API data
        api_data = fetch_api_data()
        api_date = api_data['date']
        api_solution = api_data['solution']
        
        # Decision logic
        if api_date < today:
            print(f"API date {api_date} older than today ({today}) - retry needed")
            sys.exit(1)
        elif api_date == today:
            if stored_date == today:
                print(f"Already up-to-date for {today}")
                sys.exit(0)
            else:
                # Archive previous solution if exists
                if stored_date:
                    archive_current_solution(stored_solution, stored_date)
                
                # Write new solution
                with open(DATA_FILE, 'w') as f:
                    json.dump({
                        "date": api_date,
                        "solution": api_solution
                    }, f, indent=2)
                
                print(f"Updated: {api_date} - {api_solution}")
                sys.exit(0)
        else:
            print(f"API date {api_date} is in the future (today: {today})")
            sys.exit(2)

    except Exception as e:
        print(f"Critical Error: {str(e)}")
        sys.exit(2)

if __name__ == "__main__":
    main()
