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
    return datetime.now(ET).strftime('%Y-%m-%d')

def parse_api_date(api_date_str):
    try:
        dt = datetime.strptime(api_date_str, '%b %d, %Y')
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        raise ValueError(f"Invalid API date format: {api_date_str}")

def get_current_data():
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            return {
                'solution': data.get('solution', ''),
                'date': data.get('date', ''),
                'added_utc': data.get('added_utc', '')  # New line
            }
    except (FileNotFoundError, json.JSONDecodeError):
        return {'solution': '', 'date': '', 'added_utc': ''}

def fetch_api_data():
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
                    'date': parse_api_date(raw_api_date)
                }
        raise ValueError("Bonus puzzle data not found")
    
    except Exception as e:
        print(f"API Error: {str(e)}")
        sys.exit(2)

def archive_current_solution(current_solution, current_date, current_timestamp):
    try:
        if not current_solution:
            return

        history = []
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                history = json.load(f)
        
        entry = {
            "date": current_date,
            "solution": current_solution,
            "added_utc": current_timestamp  # New field
        }
        
        if not any(e['date'] == current_date for e in history):
            history.append(entry)
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
        api_date = api_data['date']
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
                    archive_current_solution(
                        stored_data['solution'],
                        stored_data['date'],
                        stored_data.get('added_utc', datetime.utcnow().isoformat())  # Preserve timestamp
                    )
                
                with open(DATA_FILE, 'w') as f:
                    json.dump({
                        "date": api_date,
                        "solution": api_solution,
                        "added_utc": datetime.utcnow().isoformat()  # New timestamp
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
