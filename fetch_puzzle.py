import requests
import json
import sys
import os
from datetime import datetime
import pytz

API_URL = "https://www.wheeloffortune.com/api/bonus-puzzle-data"
DATA_FILE = "data.json"
HISTORY_FILE = "past-solutions.json"

def get_current_solution():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f).get('solution', '')
    except (FileNotFoundError, json.JSONDecodeError):
        return ''

def get_api_solution():
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Navigate through API structure
        for component in data.get('components', []):
            if component.get('componentName') == 'bonusPuzzle':
                puzzle_data = component.get('data', {})
                raw_solution = puzzle_data.get('solution', '')
                return ' '.join(
                    part.strip().upper() 
                    for part in raw_solution.split('/') 
                    if part.strip()
                )
                
        raise ValueError("Bonus puzzle data not found in API response")
        
    except Exception as e:
        print(f"API Error: {str(e)}")
        sys.exit(2)  # Fatal error

def archive_previous_solution():
    try:
        # Load current data
        with open(DATA_FILE, 'r') as f:
            current_data = json.load(f)
        
        # Load history
        history = []
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                history = json.load(f)
        
        # Add to history
        history.append({
            "date": datetime.now(pytz.timezone('America/New_York')).strftime('%b %d, %Y'),
            "solution": current_data.get('solution', '')
        })
        
        # Keep 1 year of history
        history = history[-365:]
        
        # Save history
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f)
            
    except Exception as e:
        print(f"Archive Error: {str(e)}")
        sys.exit(2)  # Fatal error

def main():
    current_solution = get_current_solution()
    api_solution = get_api_solution()
    
    if api_solution == current_solution:
        print("API solution matches current - retry needed")
        sys.exit(1)  # Retry code
        
    print(f"New solution detected: {api_solution}")
    
    # Archive current solution if exists
    if current_solution:
        archive_previous_solution()
    
    # Save new solution
    new_data = {
        "date": datetime.now(pytz.timezone('America/New_York')).strftime('%b %d, %Y'),
        "solution": api_solution
    }
    
    with open(DATA_FILE, 'w') as f:
        json.dump(new_data, f)
    
    sys.exit(0)  # Success

if __name__ == "__main__":
    main()
