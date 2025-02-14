import requests
import json
from datetime import datetime
import sys

API_URL = "https://www.wheeloffortune.com/api/bonus-puzzle-data"

def main():
    try:
        # Fetch current data
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()  # Raises HTTPError for bad responses
        
        new_data = response.json()
        
        # Load existing data
        try:
            with open('data.json', 'r') as f:
                existing_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_data = {"date": "", "solution": ""}
        
        # Check if new data is different
        if (new_data.get('solution') != existing_data.get('solution') or
            new_data.get('date') != existing_data.get('date')):
            
            # Save new data
            with open('data.json', 'w') as f:
                json.dump({
                    "date": new_data.get('date'),
                    "solution": new_data.get('solution').upper()
                }, f)
            
            print("Data updated successfully")
            return True
        else:
            print("No changes detected")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"Network error: {str(e)}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
