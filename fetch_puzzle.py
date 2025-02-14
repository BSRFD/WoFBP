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
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        api_data = response.json()

        puzzle_data = find_bonus_puzzle_component(api_data)
        if not puzzle_data:
            print("Error: Bonus puzzle data not found", file=sys.stderr)
            return False

        raw_solution = puzzle_data.get('solution', '')
        solution = ' '.join(
            part.strip() 
            for part in raw_solution.split('/') 
            if part.strip()
        ).upper()
        date = puzzle_data.get('date', 'Unknown date')

        with open('data.json', 'r') as f:
            existing_data = json.load(f)

        if date != existing_data.get('date') or solution != existing_data.get('solution'):
            with open('data.json', 'w') as f:
                json.dump({"date": date, "solution": solution}, f)
            
            # Update index.html timestamp to bust cache
            with open('index.html', 'r') as f:
                html = f.read()
            new_html = html.replace('?v=1.1', f'?v={int(time.time())}')
            with open('index.html', 'w') as f:
                f.write(new_html)

            print(f"Updated: {date} - {solution}")
            return True

        print("No changes detected")
        return False

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
