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

# Define distinct exit codes for different error types if desired
# This can help the bash script differentiate if needed, though exit code 2 is fine for all errors from Python
EXIT_CODE_SUCCESS = 0
EXIT_CODE_RETRY_NEEDED = 1
EXIT_CODE_API_ERROR = 2 # General API error
EXIT_CODE_HTTP_ERROR = 3 # Specific for HTTP 4xx/5xx
EXIT_CODE_NETWORK_ERROR = 4 # Specific for connection/timeout
EXIT_CODE_JSON_ERROR = 5 # Specific for JSON parsing issues
EXIT_CODE_PARSING_ERROR = 6 # Specific for custom parsing ValueErrors
EXIT_CODE_ARCHIVE_ERROR = 7
EXIT_CODE_CRITICAL_ERROR = 8 # General unhandled in main

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
    except ValueError as e: # Capture the original exception
        # This error is critical for parsing, so it will be caught by the ValueError handler in fetch_api_data
        raise ValueError(f"Invalid API date format: {api_date_str}. Original error: {e}")


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
    response = None # Initialize response to None for access in json_err block
    try:
        response = requests.get(
            API_URL,
            params={'cache_buster': time.time()},
            timeout=15 # Slightly increased timeout
        )
        response.raise_for_status() # Raises HTTPError for 4xx/5xx status codes
        data = response.json() # Raises JSONDecodeError if response is not valid JSON

        for component in data.get('components', []):
            if component.get('componentName') == 'bonusPuzzle':
                puzzle_data = component.get('data', {})
                return {
                    'solution': parse_solution(puzzle_data.get('solution', '')),
                    'date': parse_api_date(puzzle_data.get('date', '')) # Can raise ValueError
                }
        # If loop completes without returning, puzzle data was not found
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
        if response is not None:
            print(f"Response Text (first 500 chars that caused error): {response.text[:500]}", file=sys.stderr)
        else:
            print("Response object was not available for inspection.", file=sys.stderr)
        sys.exit(EXIT_CODE_JSON_ERROR)
    except ValueError as val_err: # Catches ValueErrors from parse_api_date or custom ones
        print(f"API Data Parsing Error: {val_err}", file=sys.stderr)
        sys.exit(EXIT_CODE_PARSING_ERROR)
    except Exception as e: # Generic fallback for unexpected errors within this function
        print(f"Unexpected Error in fetch_api_data: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(EXIT_CODE_API_ERROR) # Or a more generic Python error code

def archive_current_solution(current_solution, current_date):
    """Archive previous solutions"""
    try:
        if not current_solution:
            return

        history = []
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                try:
                    history = json.load(f)
                except json.JSONDecodeError as e:
                    print(f"Archive Error: Could not decode {HISTORY_FILE}. Error: {e}", file=sys.stderr)
                    # Decide if this is critical enough to exit, or try to overwrite
                    # For now, let's proceed as if it's an empty history
                    history = []

        entry = {
            "date": current_date,
            "solution": current_solution,
            "added_utc": datetime.now(timezone.utc).isoformat()
        }

        if not any(e['date'] == current_date for e in history):
            history.append(entry)
            # Ensure history doesn't grow indefinitely, keep last 365 (or your preferred limit)
            history.sort(key=lambda x: x['date'], reverse=True) # Sort to keep newest if truncating
            history = history[:365]

            with open(HISTORY_FILE, 'w') as f:
                json.dump(history, f, indent=2)

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
        api_date = api_data['date']
        api_solution = api_data['solution']

        if api_date > today:
            # This is more of an unexpected API behavior than a retryable state for *this* script's purpose.
            # Treat as an error condition that needs investigation.
            print(f"API Warning/Error: API date {api_date} is in the future (today: {today}).", file=sys.stderr)
            sys.exit(EXIT_CODE_PARSING_ERROR) # Or a specific code for this logical error
        elif api_date == today:
            if stored_data['date'] == today and stored_data['solution'] == api_solution:
                # Using stdout for normal operational messages
                print(f"Already up-to-date for {today} with solution: {api_solution}")
                sys.exit(EXIT_CODE_SUCCESS)
            else:
                # Archive previous day's solution if it exists and is different from today's new one
                if stored_data['date'] and stored_data['date'] != today : # Only archive if it's an old date
                    archive_current_solution(
                        stored_data['solution'],
                        stored_data['date']
                    )

                with open(DATA_FILE, 'w') as f:
                    json.dump({
                        "date": api_date,
                        "solution": api_solution,
                        "added_utc": datetime.now(timezone.utc).isoformat()
                    }, f, indent=2)

                # Using stdout for the success message expected by the bash script
                print(f"Updated: {api_date} - {api_solution}")
                sys.exit(EXIT_CODE_SUCCESS)
        else: # api_date < today
            # Using stdout for the retry message, as bash script might check stdout too
            print(f"API data is for {api_date}, which is older than today ({today}). Retrying is appropriate.")
            sys.exit(EXIT_CODE_RETRY_NEEDED)

    except Exception as e:
        print(f"Critical Unhandled Error in main: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(EXIT_CODE_CRITICAL_ERROR)

if __name__ == "__main__":
    main()
