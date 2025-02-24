import requests
import json
import sys
import os
from datetime import datetime
import pytz

API_URL = "https://www.wheeloffortune.com/api/bonus-puzzle-data"
DATA_FILE = "data.json"
HISTORY_FILE = "past-solutions.json"
ET = pytz.timezone('America/New_York')

def get_current_solution():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f).get('solution', '')
    except (FileNotFoundError, json.JSONDecodeError):
        return ''

def fetch_api_solution():
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        for component in data.get('components', []):
            if component.get('componentName') == 'bonusPuzzle':
                raw_solution = component.get('data', {}).get('solution', '')
                return ' '.join(
                    part.strip().upper()
                    for part in raw_solution.split('/')
                    if part.strip()
                )
        raise ValueError("Bonus puzzle data not found")
    
    except Exception as e:
        print(f"API Error: {str(e)}")
        sys.exit(2)  # Fatal error

def archive_current_solution():
    try:
        current_solution = get_current_solution()
        if not current_solution:
            return

        history = []
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                history = json.load(f)
        
        history.append({
            "date": datetime.now(ET).strftime('%b %d, %Y'),
            "solution": current_solution
        })
        
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history[-365:], f)
            
    except Exception as e:
        print(f"Archive Error: {str(e)}")
        sys.exit(2)

def main():
    try:
        current_solution = get_current_solution()
        api_solution = fetch_api_solution()
        
        if api_solution == current_solution:
            sys.exit(1)  # Retry code
            
        if current_solution:
            archive_current_solution()
            
        with open(DATA_FILE, 'w') as f:
            json.dump({
                "date": datetime.now(ET).strftime('%b %d, %Y'),
                "solution": api_solution
            }, f)
            
        print(f"Updated solution: {api_solution}")
        sys.exit(0)
        
    except Exception as e:
        print(f"Unexpected Error: {str(e)}")
        sys.exit(2)

if __name__ == "__main__":
    main()
