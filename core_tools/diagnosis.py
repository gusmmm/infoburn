import requests
import logging
import time
import random
from typing import Optional, Dict, List, Any

from rich.console import Console

# --- Configuration ---
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Constants ---
FHIR_BASE_URL = "https://r4.ontoserver.csiro.au/fhir"  # Using Ontoserver as a public FHIR server
SNOMED_SYSTEM_URL = "http://snomed.info/sct"
# ECL constraint: << means 'descendants and self of'. 404684003 is 'Clinical finding (finding)'
DIAGNOSIS_ECL_CONSTRAINT = "<<404684003"
RESULT_COUNT = 5  # How many results to request from the server (usually take the first)
MAX_RETRIES = 3
INITIAL_DELAY = 1.0

# --- Core Function ---

def find_diagnosis_snomed_code(diagnosis_term: str) -> Optional[Dict[str, str]]:
    """
    Finds a SNOMED CT code for a diagnostic term using FHIR ValueSet/$expand
    within the 'Clinical finding' hierarchy.

    This function queries a FHIR server to find SNOMED CT concepts matching
    the provided diagnosis term, constrained to descendants of 'Clinical finding'.

    Args:
        diagnosis_term: The natural language diagnostic term to search for.

    Returns:
        A dictionary {'sctid': '...', 'term': '...'} for the best match found,
        otherwise None.
    """
    if not diagnosis_term:
        logger.error("Diagnosis term cannot be empty.")
        return None

    expand_url = f"{FHIR_BASE_URL.rstrip('/')}/ValueSet/$expand"

    # Construct the 'url' parameter defining the implicit ValueSet via ECL
    valueset_url = f"{SNOMED_SYSTEM_URL}?fhir_vs=ecl/{DIAGNOSIS_ECL_CONSTRAINT}"

    params = {
        "url": valueset_url,
        "filter": diagnosis_term,
        "count": RESULT_COUNT,
    }
    headers = {"Accept": "application/fhir+json"}

    retries = 0
    delay = INITIAL_DELAY
    while retries <= MAX_RETRIES:
        logger.info(f"Querying FHIR $expand for diagnosis (Attempt {retries + 1}/{MAX_RETRIES + 1}): URL={expand_url}, Params={params}")
        try:
            response = requests.get(expand_url, params=params, headers=headers, timeout=20) # Added timeout

            # Check for non-JSON response
            if not response.headers.get('Content-Type', '').startswith('application/fhir+json'):
                 logger.error(f"Unexpected Content-Type: {response.headers.get('Content-Type')}. Response text: {response.text[:500]}")
                 return None # Don't retry if content type is wrong

            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

            # --- Success Case ---
            valueset_result = response.json()
            logger.debug(f"FHIR $expand response: {valueset_result}")

            if valueset_result.get("resourceType") != "ValueSet":
                 logger.error("Unexpected response format from $expand (not ValueSet)")
                 return None

            expansion = valueset_result.get("expansion", {})
            contains = expansion.get("contains", [])

            if not contains:
                logger.warning(f"No SNOMED CT concepts found for filter '{diagnosis_term}' within ECL '{DIAGNOSIS_ECL_CONSTRAINT}'.")
                return None # No results matching criteria

            # Assume the first result is the most relevant
            best_match = contains[0]
            sctid = best_match.get("code")
            term = best_match.get("display")

            if not sctid or not term:
                 logger.warning(f"First result found for '{diagnosis_term}' is missing code or display: {best_match}")
                 return None # Incomplete result

            logger.info(f"$expand successful: Found SCTID={sctid}, Term='{term}' for '{diagnosis_term}'")
            return {"sctid": sctid, "term": term}

        # --- Error Handling & Retry Logic ---
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response is not None else None
            response_body = ""
            if e.response is not None:
                try: response_body = e.response.json()
                except requests.exceptions.JSONDecodeError: response_body = e.response.text[:500]

            if status_code == 429 and retries < MAX_RETRIES: # Rate limit
                wait_time = delay * (2 ** retries) + random.uniform(0, 0.5)
                logger.warning(f"Rate limit hit (429) on $expand. Retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
                retries += 1
            elif status_code == 404: # Not Found
                 logger.error(f"HTTP error 404 (Not Found) querying FHIR $expand: {e}. Check FHIR base URL. Response: {response_body}")
                 return None
            elif status_code == 400: # Bad Request
                 logger.error(f"HTTP error 400 (Bad Request) querying FHIR $expand: {e}. Check parameters (URL encoding, ECL syntax?). Response: {response_body}")
                 return None
            else: # Other HTTP errors
                logger.error(f"HTTP error querying FHIR $expand: {e}. Response: {response_body}")
                if status_code and 500 <= status_code < 600 and retries < MAX_RETRIES: # Server error, retry
                    wait_time = delay * (2 ** retries) + random.uniform(0, 0.5)
                    logger.warning(f"Server error ({status_code}). Retrying in {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                    retries += 1
                else:
                    return None # Don't retry other client errors or after max retries for server errors
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e: # Network errors
            if retries < MAX_RETRIES:
                wait_time = delay * (2 ** retries) + random.uniform(0, 0.5)
                logger.warning(f"Connection/Timeout error ({type(e).__name__}) on $expand. Retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
                retries += 1
            else:
                logger.error(f"Connection/Timeout error querying FHIR $expand after {max_retries} retries: {e}")
                return None
        except requests.exceptions.JSONDecodeError as e: # Response parsing error
             logger.error(f"Failed to decode JSON response from FHIR server: {e}. Response text: {response.text[:500] if 'response' in locals() else 'N/A'}")
             return None
        except Exception as e: # Catch-all for unexpected errors
            logger.error(f"An unexpected error occurred during $expand for diagnosis: {e}", exc_info=True)
            return None

    logger.error(f"Failed to query FHIR $expand for '{diagnosis_term}' after {MAX_RETRIES + 1} attempts.")
    return None


# --- Example Usage ---
if __name__ == "__main__":
    console = Console()
    diagnoses_to_test = [
        "Myocardial infarction",
        "Diabetes mellitus type 2",
        "Pneumonia",
        "Acute respiratory distress syndrome",
        "Sepsis",
        "Headache",
        "NonExistentDiagnosisXYZ123",
        "Fracture of femur" # Example of finding outside pure 'disease' but within 'clinical finding'
    ]
    results = {}

    console.print(f"[bold blue]--- Testing Diagnosis SNOMED CT Mapping ---[/bold blue]")
    console.print(f"FHIR Server: {FHIR_BASE_URL}")
    console.print(f"SNOMED CT ECL Constraint: [cyan]{DIAGNOSIS_ECL_CONSTRAINT}[/cyan] ({'Descendants/Self of Clinical Finding'})")

    for i, term in enumerate(diagnoses_to_test):
        console.print("-" * 30)
        console.print(f"Searching for: [bold magenta]'{term}'[/bold magenta]")
        result = find_diagnosis_snomed_code(term)
        if result:
            console.print(f"  [green]Found:[/green] SCTID={result['sctid']}, Term='{result['term']}'")
        else:
            console.print("  [yellow]No valid concept found.[/yellow]")
        results[term] = result

        # Add a small delay between requests to be nice to the public server
        if i < len(diagnoses_to_test) - 1:
             sleep_duration = 1.5 # seconds
             # console.print(f"[dim]Waiting {sleep_duration}s...[/dim]")
             time.sleep(sleep_duration)

    console.print("\n[bold blue]--- Summary ---[/bold blue]")
    for term, res in results.items():
        status = f"[green]Found ({res['sctid']})[/green]" if res else "[yellow]Not Found[/yellow]"
        console.print(f"- {term}: {status}")
