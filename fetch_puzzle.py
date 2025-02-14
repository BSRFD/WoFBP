import requests
import json
import sys

API_URL = "https://www.wheeloffortune.com/api/bonus-puzzle-data"

def find_bonus_puzzle_component(data):
    """Find the bonus puzzle component in the API response"""
    if 'components' not in data:
        return None
    for component in data.get('components', []):
        if component.get('componentName') == 'bonusPuzzle':
            return component.get('data', {})
    return None

def main():
    try:
        # Fetch API data
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        api_data = response.json()

        # Find puzzle component
        puzzle_data = find_bonus_puzzle_component(api_data)
        if not puzzle_data:
            print("Error: Bonus puzzle data not found in API response", file=sys.stderr)
            return False

        # Extract and clean solution
        raw_solution = puzzle_data.get('solution', '')
        solution = ' '.join(
            part.strip() 
            for part in raw_solution.split('/') 
            if part.strip()
        ).upper()

        # Get date
        date = puzzle_data.get('date', 'Unknown date')

        # Load existing data
        try:
            with open('data.json', 'r') as f:
                existing_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_data = {"date": "", "solution": ""}

        # Check for changes
        if date != existing_data.get('date') or solution != existing_data.get('solution'):
            with open('data.json', 'w') as f:
                json.dump({
                    "date": date,
                    "solution": solution
                }, f)
            
            print(f"Updated: {date} - {solution}")
            return True

        print("No changes detected")
        return False

    except requests.exceptions.RequestException as e:
        print(f"Network error: {str(e)}", file=sys.stderr)
        return False
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {str(e)}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
