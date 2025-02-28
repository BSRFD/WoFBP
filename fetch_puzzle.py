import requests
import json
import sys
import os
import pytz

API_URL = "https://www.wheeloffortune.com/api/bonus-puzzle-data"
DATA_FILE = "data.json"
HISTORY_FILE = "past-solutions.json"
ET = pytz.timezone('America/New_York')

def get_current_data():
    """Get both solution and date from local data.json"""
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
    """Get both solution and date from API"""
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        for component in data.get('components', []):
            if component.get('componentName') == 'bonusPuzzle':
                puzzle_data = component.get('data', {})
                return {
                    'solution': self.parse_solution(puzzle_data.get('solution', '')),
                    'date': puzzle_data.get('date', '')
                }
        raise ValueError("Bonus puzzle data not found")
    
    except Exception as e:
        print(f"API Error: {str(e)}")
        sys.exit(2)

def parse_solution(raw_solution):
    """Clean and format the solution string"""
    return ' '.join(
        part.strip().upper()
        for part in raw_solution.split('/')
        if part.strip()
    )

def archive_current_solution(current_solution, current_date):
    """Archive using API-derived dates"""
    try:
        if not current_solution:
            return

        history = []
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                history = json.load(f)
        
        # Prevent duplicate entries
        if not any(entry['date'] == current_date for entry in history):
            history.append({
                "date": current_date,
                "solution": current_solution
            })
            history = history[-365:]  # Keep 1 year
            
            with open(HISTORY_FILE, 'w') as f:
                json.dump(history, f)
                
    except Exception as e:
        print(f"Archive Error: {str(e)}")
        sys.exit(2)

def main():
    try:
        # Get current stored data
        current_data = get_current_data()
        current_solution = current_data['solution']
        current_date = current_data['date']
        
        # Get latest API data
        api_data = fetch_api_data()
        api_solution = api_data['solution']
        api_date = api_data['date']
        
        # Solution unchanged - retry
        if api_solution == current_solution:
            sys.exit(1)
            
        # Archive current solution with its original API date
        if current_solution:
            archive_current_solution(current_solution, current_date)
            
        # Store new solution with its API date
        with open(DATA_FILE, 'w') as f:
            json.dump({
                "date": api_date,
                "solution": api_solution
            }, f, indent=2)
            
        print(f"Updated: {api_date} - {api_solution}")
        sys.exit(0)
        
    except Exception as e:
        print(f"Critical Error: {str(e)}")
        sys.exit(2)

if __name__ == "__main__":
    main()
