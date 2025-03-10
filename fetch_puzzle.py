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

def parse_api_date(api_date_str):
    """Convert API date (Mar 10, 2025) to YYYY-MM-DD format"""
    try:
        dt = datetime.strptime(api_date_str, '%b %d, %Y')
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        raise ValueError(f"Invalid API date format: {api_date_str}")

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
                raw_api_date = puzzle_data.get('date', '')
                return {
                    'solution': parse_solution(puzzle_data.get('solution', '')),
                    'date': parse_api_date(raw_api_date)  # FIXED HERE
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
        
        if not any(entry['date'] == current_date for entry in history):
            history.append({
                "date": current_date,
                "solution": current_solution
            })
            history = history[-365:]
            
            with open(HISTORY_FILE, 'w') as f:
                json.dump(history, f, indent=2)
                
    except Exception as e:
        print(f"Archive Error: {str(e)}")
        sys.exit(2)

def main():
    try:
        today = get_current_date()
        stored_data = get_current_data()
        
        api_data = fetch_api_data()
        api_date = api_data['date']  # Now in YYYY-MM-DD format
        api_solution = api_data['solution']

        if api_date > today:
            print(f"API date {api_date} is in the future (today: {today})")
            sys.exit(2)
        elif api_date == today:
            if stored_data['date'] == today:
                print(f"Already up-to-date for {today}")
                sys.exit(0)
            else:
                if stored_data['date']:
                    archive_current_solution(stored_data['solution'], stored_data['date'])
                
                with open(DATA_FILE, 'w') as f:
                    json.dump({
                        "date": api_date,
                        "solution": api_solution
                    }, f, indent=2)
                
                print(f"Updated: {api_date} - {api_solution}")
                sys.exit(0)
        else:
            print(f"API date {api_date} older than today ({today}) - retry needed")
            sys.exit(1)

    except Exception as e:
        print(f"Critical Error: {str(e)}")
        sys.exit(2)

if __name__ == "__main__":
    main()
