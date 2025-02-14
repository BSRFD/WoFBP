import requests
import json
from datetime import datetime

API_URL = "https://www.wheeloffortune.com/api/bonus-puzzle-data"

def main():
    # Fetch current data
    response = requests.get(API_URL)
    new_data = response.json()
    
    # Load existing data
    try:
        with open('data.json', 'r') as f:
            existing_data = json.load(f)
    except FileNotFoundError:
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
        
        print("Data updated")
    else:
        print("No changes detected")

if __name__ == "__main__":
    main()
