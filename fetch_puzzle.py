import requests
import json
import sys
import os
import pytz
import time
import traceback
from datetime import datetime, timezone

API_URL = "https://www.wheeloffortune.com/api/bonus-puzzle-data"
DATA_FILE = "data.json"
HISTORY_FILE = "past-solutions.json"
ET = pytz.timezone('America/New_York')

# Define distinct exit codes
EXIT_CODE_SUCCESS = 0
EXIT_CODE_RETRY_NEEDED = 1
EXIT_CODE_API_ERROR = 2         # For non-retryable API/request errors (e.g., 4xx)
EXIT_CODE_PARSING_ERROR = 3     # For issues parsing expected data structures (non-JSON related)
EXIT_CODE_ARCHIVE_ERROR = 4     # Kept for consistency, though not directly influencing retry
EXIT_CODE_CRITICAL_ERROR = 5    # General unhandled in main or truly critical python issues
EXIT_CODE_FUTURE_DATE_ERROR = 6 # API date is in the future

# Standard browser User-Agent
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# --- Helper for logging ---
def log_info(message):
    """Prints an informational message to stdout."""
    print(message, file=sys.stdout)

def log_warning(message):
    """Prints a warning/retryable error message to stderr."""
    print(message, file=sys.stderr)

def log_error(message):
    """Prints a critical/non-retryable error message to stderr."""
    print(f"ERROR: {message}", file=sys.stderr)
# --- End Helper ---

def parse_solution(raw_solution):
    return ' '.join(
        part.strip().upper()
        for part in raw_solution.split('/')
        if part.strip()
    )

def get_current_date_et():
    return datetime.now(ET).strftime('%Y-%m-%d')

def parse_api_date_to_yyyymmdd(api_date_str):
    try:
        dt = datetime.strptime(api_date_str, '%b %d, %Y')
        return dt.strftime('%Y-%m-%d')
    except ValueError as e:
        raise ValueError(f"Invalid API date format for '{api_date_str}'. Error: {e}")

def get_stored_data():
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

def fetch_and_parse_puzzle_data():
    response_obj = None
    try:
        log_info(f"Fetching puzzle data from API...")
        response_obj = requests.get(
            API_URL,
            params={'cache_buster': time.time()},
            timeout=20, # Increased timeout slightly
            headers=REQUEST_HEADERS
        )
        
        # Check for HTTP errors that might be retryable (5xx) or critical (4xx)
        if response_obj.status_code >= 500:
            log_warning(f"API Warning: Server error (HTTP {response_obj.status_code}). Text: {response_obj.text[:200]}. Will retry.")
            sys.exit(EXIT_CODE_RETRY_NEEDED)
        elif response_obj.status_code >= 400:
            # For 4xx errors, log as an error and exit with a non-retryable code for the bash script
            # Exception: 429 Too Many Requests might be retryable with a longer delay,
            # but for now, we'll treat most 4xx as needing investigation.
            log_error(f"API HTTP Error {response_obj.status_code}: {response_obj.text[:200]}. Not automatically retryable by this script.")
            sys.exit(EXIT_CODE_API_ERROR)
        
        # If we got here, status code was < 400, likely 200 OK.
        # Proceed to parse JSON.
        try:
            api_json_data = response_obj.json()
        except json.JSONDecodeError as e:
            log_warning(f"API Warning: Could not decode JSON from API response. Error: {e}. Response text (first 200 chars): {response_obj.text[:200]}. Will retry.")
            sys.exit(EXIT_CODE_RETRY_NEEDED)

        for component in api_json_data.get('components', []):
            if component.get('componentName') == 'bonusPuzzle':
                puzzle_data_obj = component.get('data', {})
                
                api_date_raw = puzzle_data_obj.get('date', '')
                api_solution_raw = puzzle_data_obj.get('solution', '')

                if not api_date_raw and not api_solution_raw:
                    log_warning(f"API Info: Puzzle date and solution not found in API response (likely not yet posted). Raw puzzle_data keys: {list(puzzle_data_obj.keys())}. Will retry.")
                    sys.exit(EXIT_CODE_RETRY_NEEDED)
                if not api_date_raw:
                    log_warning(f"API Data Inconsistency: Solution found ('{api_solution_raw[:30]}...') but date is missing. Will retry.")
                    sys.exit(EXIT_CODE_RETRY_NEEDED) # Treat as retryable, might be transient
                if not api_solution_raw : #Technically covered by the first check, but good for clarity
                    log_warning(f"API Data Inconsistency: Date found ('{api_date_raw}') but solution is missing. Will retry.")
                    sys.exit(EXIT_CODE_RETRY_NEEDED) # Treat as retryable

                # If we are here, both date and solution strings were found
                try:
                    parsed_date_yyyymmdd = parse_api_date_to_yyyymmdd(api_date_raw)
                except ValueError as e:
                    log_warning(f"API Warning: Found date '{api_date_raw}' but could not parse it. Error: {e}. Will retry.")
                    sys.exit(EXIT_CODE_RETRY_NEEDED) # If format changes, might be temp
                
                parsed_solution_str = parse_solution(api_solution_raw)
                log_info(f"API Success: Found puzzle for date {parsed_date_yyyymmdd} with solution '{parsed_solution_str}'.")
                return {'date': parsed_date_yyyymmdd, 'solution': parsed_solution_str}
        
        log_warning("API Warning: 'bonusPuzzle' component or its data not found in expected structure. Will retry.")
        sys.exit(EXIT_CODE_RETRY_NEEDED)

    except requests.exceptions.Timeout as e:
        log_warning(f"Network Warning: API request timed out. Error: {e}. Will retry.")
        sys.exit(EXIT_CODE_RETRY_NEEDED)
    except requests.exceptions.ConnectionError as e:
        log_warning(f"Network Warning: API connection error. Error: {e}. Will retry.")
        sys.exit(EXIT_CODE_RETRY_NEEDED)
    except requests.exceptions.RequestException as e: # Other, less common request errors
        log_error(f"API Request Error: {e}. This might be critical.") # More generic, might be non-retryable
        sys.exit(EXIT_CODE_API_ERROR)
    # ValueError from parse_api_date is caught above and made retryable.
    # Other ValueErrors here would be unexpected.
    except Exception as e: # Generic fallback for truly unexpected errors within this function
        log_error(f"Unexpected error in fetch_and_parse_puzzle_data: {str(e)}")
        traceback.print_exc(file=sys.stderr)
        sys.exit(EXIT_CODE_CRITICAL_ERROR) # Use a distinct critical error code

def archive_solution_if_needed(solution_to_archive, date_to_archive):
    if not solution_to_archive and not date_to_archive:
        return

    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                history = json.load(f)
            if not isinstance(history, list):
                log_warning(f"Archive Warning: {HISTORY_FILE} was not a list. Reinitializing.")
                history = []
        except json.JSONDecodeError as e:
            log_warning(f"Archive Warning: Could not decode {HISTORY_FILE}. Error: {e}. Reinitializing.")
            history = []
        except Exception as e:
            log_error(f"Archive Error: Failed to load {HISTORY_FILE}. Error: {e}")
            sys.exit(EXIT_CODE_ARCHIVE_ERROR) # Archiving is important, make this critical if load fails

    entry = {
        "date": date_to_archive,
        "solution": solution_to_archive,
        "added_utc": datetime.now(timezone.utc).isoformat()
    }

    if not any(e.get('date') == date_to_archive for e in history):
        history.append(entry)
        history.sort(key=lambda x: x.get('date', ''), reverse=True)
        history = history[:365]
        try:
            with open(HISTORY_FILE, 'w') as f:
                json.dump(history, f, indent=2)
            log_info(f"Archived previous solution for {date_to_archive}.")
        except Exception as e:
            log_error(f"Archive Error: Failed to write to {HISTORY_FILE}. Error: {e}")
            sys.exit(EXIT_CODE_ARCHIVE_ERROR)
    else:
        log_info(f"Archive: Solution for {date_to_archive} already in history.")


def main():
    try:
        today_et_yyyymmdd = get_current_date_et()
        log_info(f"Script started. Today (ET) is {today_et_yyyymmdd}.")
        
        stored_puzzle_data = get_stored_data()
        log_info(f"Current stored data: Date='{stored_puzzle_data.get('date')}', Solution='{stored_puzzle_data.get('solution', '')[:30]}...'")

        # This function will sys.exit with EXIT_CODE_RETRY_NEEDED for most transient issues
        # or other codes for success/critical failure.
        api_puzzle_data = fetch_and_parse_puzzle_data() 
        
        api_date = api_puzzle_data['date']
        api_solution = api_puzzle_data['solution']

        if api_date > today_et_yyyymmdd:
            log_error(f"API date {api_date} is in the future (today: {today_et_yyyymmdd}). This is unexpected.")
            sys.exit(EXIT_CODE_FUTURE_DATE_ERROR) # This is a specific non-retryable error
        
        elif api_date == today_et_yyyymmdd:
            if stored_puzzle_data.get('date') == today_et_yyyymmdd and \
               stored_puzzle_data.get('solution') == api_solution:
                log_info(f"Puzzle already up-to-date for {today_et_yyyymmdd}: '{api_solution}'. No change needed.")
                sys.exit(EXIT_CODE_SUCCESS)
            else:
                log_info(f"New puzzle data for today ({api_date}): '{api_solution}'. Updating.")
                if stored_puzzle_data.get('date') and stored_puzzle_data.get('date') != api_date:
                     archive_solution_if_needed(stored_puzzle_data.get('solution'), stored_puzzle_data.get('date'))
                
                with open(DATA_FILE, 'w') as f:
                    json.dump({
                        "date": api_date,
                        "solution": api_solution,
                        "added_utc": datetime.now(timezone.utc).isoformat()
                    }, f, indent=2)
                
                # This is the primary success output for the bash script
                print(f"Updated: {api_date} - {api_solution}") 
                sys.exit(EXIT_CODE_SUCCESS)
        
        else: # api_date < today_et_yyyymmdd
            log_warning(f"API data is old (API date: {api_date}, Today: {today_et_yyyymmdd}). Will retry for current data.")
            sys.exit(EXIT_CODE_RETRY_NEEDED)

    except SystemExit: # Allow sys.exit() to propagate
        raise
    except Exception as e:
        log_error(f"Critical unhandled error in main: {str(e)}")
        traceback.print_exc(file=sys.stderr)
        sys.exit(EXIT_CODE_CRITICAL_ERROR)

if __name__ == "__main__":
    main()
