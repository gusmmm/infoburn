import requests
import logging
import time
import random
from typing import Optional, Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def find_snomed_code_fhir_expand(medication_name: str) -> Optional[Dict[str, str]]:
    """
    Finds a SNOMED CT code for a medication name using FHIR ValueSet/$expand
    with an ECL constraint and a text filter, optimized for Snowstorm FHIR API.

    This method searches within a specified SNOMED CT hierarchy (defined by ECL)
    for concepts matching the filter text.

    Args:
        medication_name: The name of the medication to search for (used in 'filter').

    Returns:
        A dictionary {'sctid': '...', 'term': '...'} for the best match found,
        otherwise None.
    """
    # Constants that were previously parameters
    fhir_base_url = "https://r4.ontoserver.csiro.au/fhir"  # Using Ontoserver as more stable option
    snomed_system_url = "http://snomed.info/sct"
    ecl_constraint = "<<763158003"  # ECL constraint: << means 'descendants and self of'. 763158003 is 'Medicinal product (product)'
    result_count = 5  # How many results to request from the server
    max_retries = 3
    initial_delay = 1.0

    if not medication_name:
        logger.error("Medication name cannot be empty.")
        return None

    expand_url = f"{fhir_base_url.rstrip('/')}/ValueSet/$expand"

    # Construct the 'url' parameter defining the implicit ValueSet via ECL
    valueset_url = f"{snomed_system_url}?fhir_vs=ecl/{ecl_constraint}"

    params = {
        "url": valueset_url,
        "filter": medication_name,
        "count": result_count,
    }
    headers = {"Accept": "application/fhir+json"}

    retries = 0
    delay = initial_delay
    while retries <= max_retries:
        logger.info(f"Querying FHIR $expand (Attempt {retries + 1}/{max_retries + 1}): URL={expand_url}, Params={params}")
        try:
            response = requests.get(expand_url, params=params, headers=headers, timeout=20)

            # Check for non-JSON response (common with browser endpoint if URL is wrong)
            if not response.headers.get('Content-Type', '').startswith('application/fhir+json'):
                 logger.error(f"Unexpected Content-Type: {response.headers.get('Content-Type')}. Response text: {response.text[:500]}")
                 # Don't retry if the content type is wrong, likely a fundamental URL/server issue
                 return None

            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

            # --- Success Case ---
            valueset_result = response.json()
            logger.debug(f"FHIR $expand response: {valueset_result}")

            if valueset_result.get("resourceType") != "ValueSet":
                 logger.error("Unexpected response format from $expand (not ValueSet)")
                 return None # Unexpected response format

            # Check the expansion contains element
            expansion = valueset_result.get("expansion", {})
            contains = expansion.get("contains", [])

            if not contains:
                logger.warning(f"No concepts found for filter '{medication_name}' within ECL '{ecl_constraint}'.")
                return None # Search successful, but no results matching criteria

            # Assume the first result is the most relevant
            # Servers often rank results, but this isn't guaranteed by FHIR spec
            best_match = contains[0]
            sctid = best_match.get("code")
            term = best_match.get("display")

            if not sctid or not term:
                 logger.warning(f"First result found for '{medication_name}' is missing code or display: {best_match}")
                 # Try the next result if the first is incomplete? For now, fail.
                 return None

            logger.info(f"$expand successful: Found SCTID={sctid}, Term='{term}' for '{medication_name}'")
            # No separate semantic tag check needed as ECL constraint already filters by hierarchy
            return {"sctid": sctid, "term": term}

        # --- Error Handling & Retry Logic ---
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response is not None else None
            # Log response body for debugging client errors (like 400)
            response_body = ""
            if e.response is not None:
                try:
                    response_body = e.response.json() # Try parsing as JSON (OperationOutcome)
                except requests.exceptions.JSONDecodeError:
                    response_body = e.response.text[:500] # Otherwise take raw text

            if status_code == 429 and retries < max_retries:
                wait_time = delay * (2 ** retries) + random.uniform(0, 0.5)
                logger.warning(f"Rate limit hit (429) on $expand. Retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
                retries += 1
            elif status_code == 404:
                 logger.error(f"HTTP error 404 (Not Found) querying FHIR $expand: {e}. Check FHIR base URL. Response: {response_body}")
                 return None
            elif status_code == 400:
                 logger.error(f"HTTP error 400 (Bad Request) querying FHIR $expand: {e}. Check parameters (URL encoding, ECL syntax?). Response: {response_body}")
                 return None
            else:
                logger.error(f"HTTP error querying FHIR $expand: {e}. Response: {response_body}")
                if status_code and 500 <= status_code < 600 and retries < max_retries:
                    wait_time = delay * (2 ** retries) + random.uniform(0, 0.5)
                    logger.warning(f"Server error ({status_code}). Retrying in {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                    retries += 1
                else:
                    return None # Don't retry other client errors or after max retries for server errors
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            if retries < max_retries:
                wait_time = delay * (2 ** retries) + random.uniform(0, 0.5)
                logger.warning(f"Connection/Timeout error ({type(e).__name__}) on $expand. Retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
                retries += 1
            else:
                logger.error(f"Connection/Timeout error querying FHIR $expand after {max_retries} retries: {e}")
                return None
        except requests.exceptions.JSONDecodeError as e:
             logger.error(f"Failed to decode JSON response from FHIR server: {e}. Response text: {response.text[:500] if 'response' in locals() else 'N/A'}")
             return None # Cannot process non-JSON response
        except Exception as e:
            logger.error(f"An unexpected error occurred during $expand: {e}", exc_info=True)
            return None

    logger.error(f"Failed to query FHIR $expand for '{medication_name}' after {max_retries + 1} attempts.")
    return None


# --- Example Usage (with delays between calls) ---
if __name__ == "__main__":
    medications_to_test = ["Lisinopril", "Metformin", "Aspirin", "NonExistentMedicationXYZ", "Amoxicillin"]
    results = {}

    print(f"--- Testing against FHIR Server ($expand): https://r4.ontoserver.csiro.au/fhir ---")
    print(f"--- Using ECL constraint: { '<<763158003' } ---") # Default ECL

    for med_name in medications_to_test:
        print("-" * 20)
        result = find_snomed_code_fhir_expand(med_name)
        print(f"Search for '{med_name}': {result}")
        results[med_name] = result
        if med_name != medications_to_test[-1]:
             sleep_duration = 1.5
             print(f"Waiting for {sleep_duration} seconds before next request...")
             time.sleep(sleep_duration)

    print("\n--- Summary ---")
    for med, res in results.items():
        print(f"{med}: {res}")

    # Example: Search for a substance instead of a product
    print("-" * 20)
    substance_ecl = "<<105590001" # ECL for Substance hierarchy
    print(f"Searching for 'Aspirin' within Substance hierarchy (ECL: {substance_ecl})")
    result_substance = find_snomed_code_fhir_expand("Aspirin")
    print(f"Search for 'Aspirin' (substance): {result_substance}")