import requests
import json
import sys
import datetime
import pytz

API_URL = "https://www.wheeloffortune.com/api/bonus-puzzle-data"

def should_check_today():
    """Check if current time is within our monitoring window"""
    eastern = pytz.timezone('America/New_York')
    now = datetime.datetime.now(eastern)
    
    # Only check Mon-Fri between 16:50 and 17:20 ET
    if now.weekday() >= 5:  # 5=Saturday, 6=Sunday
        return False
        
    current_time = now.time()
    return datetime.time(16, 50) <= current_time <= datetime.time(17, 20)

def main():
    if not should_check_today():
        print("Outside monitoring window")
        return False

    try:
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

        # Find puzzle data
        puzzle_data = None
        for component in api_data.get('components', []):
            if component.get('componentName') == 'bonusPuzzle':
                puzzle_data = component.get('data', {})
                break

        if not puzzle_data:
            print("Puzzle data not found")
            return False

        # Process solution
        raw_solution = puzzle_data.get('solution', '')
        solution = ' '.join(
            part.strip() 
            for part in raw_solution.split('/') 
            if part.strip()
        ).upper()
        new_date = puzzle_data.get('date', 'Unknown date')

        # Check if we already have this solution
        if new_date == existing_data.get('date'):
            print("Already have today's solution")
            return False

        # Update data
        with open('data.json', 'w') as f:
            json.dump({
                "date": new_date,
                "solution": solution
            }, f)

        print(f"Updated {new_date}: {solution}")
        return True

    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
