import requests
import json
import sys

API_URL = "https://www.wheeloffortune.com/api/bonus-puzzle-data"

def main():
    try:
        print(f"Attempting to fetch data from {API_URL}")
        response = requests.get(API_URL, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.text[:200]}")  # Show first 200 characters
        
        new_data = response.json()
        print(f"Parsed JSON: {new_data}")

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
