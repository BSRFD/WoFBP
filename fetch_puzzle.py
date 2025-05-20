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

# Standard browser User-Agent
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

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
    response_obj = None
    try:
        cache_buster_value = time.time()
        print(f"DEBUG: Fetching API data from {API_URL} with cache_buster={cache_buster_value}", file=sys.stderr)
        print(f"DEBUG: Using headers: {json.dumps(REQUEST_HEADERS)}", file=sys.stderr)

        response_obj = requests.get(
            API_URL,
            params={'cache_buster': cache_buster_value},
            timeout=15,
            headers=REQUEST_HEADERS # MODIFICATION: Added User-Agent header
        )
        response_obj.raise_for_status()
        
        # Attempt to decode JSON, log raw text on failure for better debugging
        try:
            data = response_obj.json()
        except json.JSONDecodeError as json_decode_err:
            print(f"DEBUG: JSONDecodeError occurred. Raw response text (first 2000 chars) that caused error:\n{response_obj.text[:2000]}", file=sys.stderr)
            raise json_decode_err # Re-raise the original error to be caught by the outer handler

        print(f"DEBUG: Raw API response JSON parsed. Top-level keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}", file=sys.stderr)
        # print(f"DEBUG: Full raw API response data (might be very long, first 2000 chars for safety):\n{str(data)[:2000]}", file=sys.stderr)


        for component in data.get('components', []):
            if component.get('componentName') == 'bonusPuzzle':
                puzzle_data = component.get('data', {})
                print(f"DEBUG: Found 'bonusPuzzle' component. Raw puzzle_data content: {json.dumps(puzzle_data)}", file=sys.stderr)

                api_date_str = puzzle_data.get('date', '')
                api_solution_str = puzzle_data.get('solution', '')
                print(f"DEBUG: Extracted api_date_str='{api_date_str}', api_solution_str='{api_solution_str}'", file=sys.stderr)

                if not api_date_str:
                    if not api_solution_str:
                        print("API Info: Both date and solution are effectively empty from API (keys might be missing or values are empty). Assuming no puzzle available yet.", file=sys.stderr)
                        # MODIFICATION: Log more of the response when this specific condition is met
                        print(f"DEBUG: Full response text when date/solution were empty in puzzle_data (first 2000 chars of response_obj.text):\n{response_obj.text[:2000]}", file=sys.stderr)
                        sys.exit(EXIT_CODE_RETRY_NEEDED)
                    else:
                        print("API Data Inconsistency: API returned an empty date string but a non-empty solution.", file=sys.stderr)
                        sys.exit(EXIT_CODE_PARSING_ERROR)

                parsed_date = parse_api_date(api_date_str)
                parsed_solution = parse_solution(api_solution_str)

                return {
                    'solution': parsed_solution,
                    'date': parsed_date
                }
        
        print("DEBUG: 'bonusPuzzle' component or its 'data' key was not found or was structured unexpectedly in the API response.", file=sys.stderr)
        print(f"DEBUG: Full response text when 'bonusPuzzle' data structure was not found (first 2000 chars of response_obj.text):\n{response_obj.text[:2000]}", file=sys.stderr)
        raise ValueError("Bonus puzzle data structure not found or incomplete in API response.")

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
    except requests.exceptions.RequestException as req_err:
        print(f"API Request Error: {req_err}", file=sys.stderr)
        sys.exit(EXIT_CODE_API_ERROR)
    except json.JSONDecodeError as json_err: # This will now catch the re-raised error too
        print(f"API JSON Decode Error: {json_err}", file=sys.stderr)
        # response_obj might be None if error happened before request, but usually available
        if response_obj and hasattr(response_obj, 'text'):
            print(f"Response Text (first 500 chars that might have caused error): {response_obj.text[:500]}", file=sys.stderr)
        else:
            print("Response object or its text was not available for inspection.", file=sys.stderr)
        sys.exit(EXIT_CODE_JSON_ERROR)
    except ValueError as val_err:
        print(f"API Data Parsing/Integrity Error: {val_err}", file=sys.stderr)
        sys.exit(EXIT_CODE_PARSING_ERROR)
    except Exception as e:
        print(f"Unexpected Error in fetch_api_data: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(EXIT_CODE_API_ERROR)

def archive_current_solution(current_solution, current_date):
    """Archive previous solutions"""
    try:
        if not current_solution and not current_date:
            print("Archive Info: Nothing to archive (current solution and date are empty).", file=sys.stdout)
            return

        history = []
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                try:
                    history = json.load(f)
                    if not isinstance(history, list):
                        print(f"Archive Warning: {HISTORY_FILE} did not contain a list. Reinitializing.", file=sys.stderr)
                        history = []
                except json.JSONDecodeError as e:
                    print(f"Archive Warning: Could not decode {HISTORY_FILE}. Error: {e}. Reinitializing.", file=sys.stderr)
                    history = []

        entry = {
            "date": current_date,
            "solution": current_solution,
            "added_utc": datetime.now(timezone.utc).isoformat()
        }

        if not any(e.get('date') == current_date for e in history):
            history.append(entry)
            history.sort(key=lambda x: x.get('date', ''), reverse=True)
            history = history[:365]

            with open(HISTORY_FILE, 'w') as f:
                json.dump(history, f, indent=2)
            print(f"Archive Info: Archived solution for {current_date}.", file=sys.stdout)
        else:
            print(f"Archive Info: Entry for date {current_date} already exists. Not re-archiving.", file=sys.stdout)

    except Exception as e:
        print(f"Error during archiving: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(EXIT_CODE_ARCHIVE_ERROR)

def main():
    try:
        today = get_current_date()
        print(f"DEBUG: Current ET date (today): {today}", file=sys.stderr)
        stored_data = get_current_data()
        print(f"DEBUG: Stored data: {stored_data}", file=sys.stderr)

        api_data = fetch_api_data()
        api_date = api_data['date']
        api_solution = api_data['solution']
        print(f"DEBUG: API data received and parsed: date='{api_date}', solution='{api_solution}'", file=sys.stderr)

        if api_date > today:
            print(f"API Error: API date {api_date} is in the future (today: {today}). This is unexpected.", file=sys.stderr)
            sys.exit(EXIT_CODE_FUTURE_DATE_ERROR)
        elif api_date == today:
            if stored_data.get('date') == today and stored_data.get('solution') == api_solution:
                print(f"Already up-to-date for {today} with solution: {api_solution}")
                sys.exit(EXIT_CODE_SUCCESS)
            else:
                if stored_data.get('date') and stored_data.get('date') != api_date: # Only archive if dates differ
                    print(f"DEBUG: Archiving old stored data: date='{stored_data.get('date')}', solution='{stored_data.get('solution')}'", file=sys.stderr)
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
                print(f"Updated: {api_date} - {api_solution}")
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
