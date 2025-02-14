import requests
import json
import sys

API_URL = "https://www.wheeloffortune.com/api/bonus-puzzle-data"

def main():
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        new_data = response.json()

        # Validate API response
        if not isinstance(new_data, dict) or 'solution' not in new_data:
            print("Invalid API response format", file=sys.stderr)
            return False

        # Handle null/None solution
        raw_solution = new_data.get('solution') or ''
        solution = raw_solution.upper() if raw_solution else ''

        # Load existing data
        try:
            with open('data.json', 'r') as f:
                existing_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_data = {"date": "", "solution": ""}

        # Check for changes
        if (new_data.get('date') != existing_data.get('date') or
            solution != existing_data.get('solution')):

            with open('data.json', 'w') as f:
                json.dump({
                    "date": new_data.get('date', ''),
                    "solution": solution
                }, f)
            
            print("Data updated successfully")
            return True

        print("No changes detected")
        return False

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
