import requests
import json
import sys
import os
import pytz
import time
import traceback # For detailed tracebacks in generic exceptions
from datetime import datetime, timezone

API_URL = "https://www.wheeloffortune.com/api/bonus-puzzle-data"
DATA_FILE = "data.json"
HISTORY_FILE = "past-solutions.json"
ET = pytz.timezone('America/New_York')

# Define distinct exit codes
EXIT_CODE_SUCCESS = 0
EXIT_CODE_RETRY_NEEDED = 1
EXIT_CODE_API_ERROR = 2         # General API error (less specific network/request error)
EXIT_CODE_HTTP_ERROR = 3        # Specific for HTTP 4xx/5xx
EXIT_CODE_NETWORK_ERROR = 4     # Specific for connection/timeout
EXIT_CODE_JSON_ERROR = 5        # Specific for JSON parsing issues
EXIT_CODE_PARSING_ERROR = 6     # Specific for custom parsing ValueErrors / inconsistent data
EXIT_CODE_ARCHIVE_ERROR = 7
EXIT_CODE_CRITICAL_ERROR = 8    # General unhandled in main
EXIT_CODE_FUTURE_DATE_ERROR = 9 # API date is in the future

def parse_solution(raw_solution):
    """Clean and format the solution string"""
    return ' '.join(
        part.strip().upper()
        for part in raw_solution.split('/')
        if part.strip()
    )

def get_current_date():
    """Get current ET date in YYYY-MM-DD format"""
    return datetime.now(ET).strftime('%Y-%m-%d')

def parse_api_date(api_date_str):
    """Convert API date (Mar 10, 2025) to YYYY-MM-DD format"""
    try:
        dt = datetime.strptime(api_date_str, '%b %d, %Y')
        return dt.strftime('%Y-%m-%d')
    except ValueError as e:
        # This error is critical for parsing, it will be caught by the ValueError handler in fetch_api_data
        raise ValueError(f"Invalid API date format for input '{api_date_str}'. Original error: {e}")


def get_current_data():
    """Get stored solution and date from data.json"""
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            return {
                'solution': data.get('solution', ''),
                'date': data.get('date', ''),
                'added_utc': data.get('added_utc', '')
            }
    except (FileNotFoundError, json.JSONDecodeError):
        return {'solution': '', 'date': '', 'added_utc': ''}

def fetch_api_data():
    """Fetch and parse API data with cache busting and improved error handling"""
    response_obj = None # Initialize for access in json_err block
    try:
        response_obj = requests.get(
            API_URL,
            params={'cache_buster': time.time()},
            timeout=15
        )
        response_obj.raise_for_status() # Raises HTTPError for 4xx/5xx status codes
        data = response_obj.json()    # Raises JSONDecodeError if response is not valid JSON

        for component in data.get('components', []):
            if component.get('componentName') == 'bonusPuzzle':
                puzzle_data = component.get('data', {})

                api_date_str = puzzle_data.get('date', '')       # Default to empty string if 'date' key is missing
                api_solution_str = puzzle_data.get('solution', '') # Default to empty string

                if not api_date_str: # Check if the date string from API is empty
                    if not api_solution_str:
                        # Both date and solution are empty - most likely puzzle not yet available
                        print("API Info: Both date and solution are empty from API. Assuming no puzzle available yet.", file=sys.stderr)
                        sys.exit(EXIT_CODE_RETRY_NEEDED)
                    else:
                        # Date is empty but solution is not - this is unexpected/inconsistent data
                        print("API Data Inconsistency: API returned an empty date string but a non-empty solution.", file=sys.stderr)
                        # This will be caught by the ValueError catch-all below if we raise it,
                        # or we can exit with a specific code here.
                        # For clarity, let's make it a specific exit.
                        sys.exit(EXIT_CODE_PARSING_ERROR)

                # If we reach here, api_date_str was not empty.
                parsed_date = parse_api_date(api_date_str) # Can raise ValueError if format is wrong despite not being empty
                parsed_solution = parse_solution(api_solution_str) # Should be safe even if solution_str is empty

                return {
                    'solution': parsed_solution,
                    'date': parsed_date
                }
        # If loop completes without returning, bonusPuzzle component or its data was not found
        raise ValueError("Bonus puzzle data structure not found in API response.")

    except requests.exceptions.HTTPError as http_err:
        print(f"API HTTP Error: {http_err}", file=sys.stderr)
        if http_err.response is not None:
            print(f"Status Code: {http_err.response.status_code}", file=sys.stderr)
            print(f"Response Text (first 500 chars): {http_err.response.text[:500]}", file=sys.stderr)
        sys.exit(EXIT_CODE_HTTP_ERROR)
    except requests.exceptions.Timeout as timeout_err:
        print(f"API Timeout Error: {timeout_err}", file=sys.stderr)
        sys.exit(EXIT_CODE_NETWORK_ERROR)
    except requests.exceptions.ConnectionError as conn_err:
        print(f"API Connection Error: {conn_err}", file=sys.stderr)
        sys.exit(EXIT_CODE_NETWORK_ERROR)
    except requests.exceptions.RequestException as req_err: # Catch other request-related errors
        print(f"API Request Error: {req_err}", file=sys.stderr)
        sys.exit(EXIT_CODE_API_ERROR)
    except json.JSONDecodeError as json_err:
        print(f"API JSON Decode Error: {json_err}", file=sys.stderr)
        if response_obj is not None:
            print(f"Response Text (first 500 chars that caused error): {response_obj.text[:500]}", file=sys.stderr)
        else:
            print("Response object was not available for inspection.", file=sys.stderr)
        sys.exit(EXIT_CODE_JSON_ERROR)
    except ValueError as val_err: # Catches ValueErrors from parse_api_date or custom ones like "Bonus puzzle data structure not found"
        print(f"API Data Parsing/Integrity Error: {val_err}", file=sys.stderr)
        sys.exit(EXIT_CODE_PARSING_ERROR)
    except Exception as e: # Generic fallback for unexpected errors within this function
        print(f"Unexpected Error in fetch_api_data: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(EXIT_CODE_API_ERROR)

def archive_current_solution(current_solution, current_date):
    """Archive previous solutions"""
    try:
        if not current_solution and not current_date: # Nothing to archive if both are empty
            return

        history = []
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                try:
                    history = json.load(f)
                    if not isinstance(history, list): # Ensure history is a list
                        print(f"Archive Warning: {HISTORY_FILE} did not contain a list. Reinitializing.", file=sys.stderr)
                        history = []
                except json.JSONDecodeError as e:
                    print(f"Archive Warning: Could not decode {HISTORY_FILE}. Error: {e}. Reinitializing.", file=sys.stderr)
                    history = []

        entry = {
            "date": current_date, # Assumed to be valid if passed here
            "solution": current_solution,
            "added_utc": datetime.now(timezone.utc).isoformat()
        }

        # Avoid duplicate entries for the same date
        if not any(e.get('date') == current_date for e in history):
            history.append(entry)
            # Sort by date descending to easily manage the size limit
            history.sort(key=lambda x: x.get('date', ''), reverse=True)
            history = history[:365] # Keep the most recent 365 entries

            with open(HISTORY_FILE, 'w') as f:
                json.dump(history, f, indent=2)
        else:
            print(f"Archive Info: Entry for date {current_date} already exists. Not re-archiving.", file=sys.stdout)


    except Exception as e:
        print(f"Error during archiving: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(EXIT_CODE_ARCHIVE_ERROR)

def main():
    try:
        today = get_current_date()
        stored_data = get_current_data()

        # fetch_api_data will sys.exit on its own if there's an issue
        api_data = fetch_api_data()
        api_date = api_data['date']         # This comes from parsed_date
        api_solution = api_data['solution'] # This comes from parsed_solution

        if api_date > today:
            print(f"API Error: API date {api_date} is in the future (today: {today}). This is unexpected.", file=sys.stderr)
            sys.exit(EXIT_CODE_FUTURE_DATE_ERROR)
        elif api_date == today:
            if stored_data.get('date') == today and stored_data.get('solution') == api_solution:
                print(f"Already up-to-date for {today} with solution: {api_solution}")
                sys.exit(EXIT_CODE_SUCCESS)
            else:
                # Archive the old stored data only if its date is different from today's API date
                # and if there was actually old data.
                if stored_data.get('date') and stored_data.get('date') != api_date:
                    archive_current_solution(
                        stored_data.get('solution'),
                        stored_data.get('date')
                    )

                with open(DATA_FILE, 'w') as f:
                    json.dump({
                        "date": api_date,
                        "solution": api_solution,
                        "added_utc": datetime.now(timezone.utc).isoformat()
                    }, f, indent=2)

                print(f"Updated: {api_date} - {api_solution}") # Expected by bash script for commit
                sys.exit(EXIT_CODE_SUCCESS)
        else: # api_date < today
            print(f"API data is for {api_date}, which is older than today ({today}). Retrying is appropriate.")
            sys.exit(EXIT_CODE_RETRY_NEEDED)

    except Exception as e:
        print(f"Critical Unhandled Error in main: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(EXIT_CODE_CRITICAL_ERROR)

if __name__ == "__main__":
    main()
