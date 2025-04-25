import os
from typing import Optional
import traceback # Import traceback for detailed error logging

# Google GenAI SDK
from google import genai
from google.genai import types
from google.api_core import exceptions as google_exceptions

# Environment and Rich UI
from dotenv import load_dotenv
from rich.console import Console
from rich.console import Console
from rich.table import Table # Import Table for displaying models
# --- Configuration ---
# Load environment variables from .env file if it exists
load_dotenv()

class GenAIClientManager:
    """
    Manages the initialization and configuration of the Google Gemini API client.

    This class centralizes the logic for loading the API key from environment
    variables and creating a configured `google.genai.Client` instance,
    providing a single point of setup for various extractor services.
    """

    def __init__(self, console: Optional[Console] = None):
        """
        Initializes the GenAIClientManager.

        Args:
            console: An optional rich.console.Console instance for logging.
                     If None, a new Console instance will be created.
        """
        self.console = console if console else Console()
        self.api_key: Optional[str] = None

    def _load_api_key(self) -> str:
        """
        Loads the Gemini API key from the GEMINI_API_KEY environment variable.

        Logs success or failure using the provided console.

        Returns:
            The API key string.

        Raises:
            ValueError: If the GEMINI_API_KEY environment variable is not found.
        """
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            self.console.print("[bold red]Error: GEMINI_API_KEY environment variable not found.[/bold red]")
            raise ValueError("GEMINI_API_KEY environment variable not found.")
        self.console.print("[green]✓ Gemini API key loaded successfully.[/green]")
        self.api_key = api_key
        return api_key

    def get_client(self) -> genai.Client:
        """
        Initializes and returns a Google Gemini API client instance.

        It first ensures the API key is loaded using `_load_api_key`.
        It uses the loaded API key to configure and create the client.

        Returns:
            An initialized `google.genai.Client` instance.

        Raises:
            ValueError: If the API key cannot be loaded or if client
                        initialization fails.
        """
        # Ensure API key is loaded
        if not self.api_key:
            self._load_api_key() # This will raise ValueError if key is missing

        try:
            # Initialize the client using the API key
            # Consistent with the pattern in existing extractors:
            # burns_extractor.py, medication_extractor.py, medical_history_extractor.py, case_extracter.py
            client = genai.Client(api_key=self.api_key)

            self.console.print("[green]✓ Gemini client initialized successfully.[/green]")
            return client
        except google_exceptions.GoogleAPIError as api_err:
            self.console.print(f"[bold red]Google API Error during client initialization: {api_err}[/bold red]")
            raise ValueError(f"Failed to initialize Gemini client due to API error: {api_err}")
        except Exception as e:
            # Catch any other unexpected errors during client initialization
            self.console.print(f"[bold red]Unexpected error initializing Gemini client: {e}[/bold red]")
            self.console.print(f"[grey50]{traceback.format_exc()}[/grey50]")
            raise ValueError(f"Failed to initialize Gemini client: {e}")

# --- Example Usage & Basic Tests ---
if __name__ == "__main__":
    console = Console()
    console.print("[bold cyan]--- Testing GenAIClientManager ---[/bold cyan]")

    manager = GenAIClientManager(console=console)
    client_instance_for_tests: Optional[genai.Client] = None # Variable to hold client for tests

    # Test 1: Get Client (Happy Path)
    console.print("\n[yellow]Test 1: Attempting to get client...[/yellow]")
    try:
        client_instance_for_tests = manager.get_client() # Store client for later tests
        console.print(f"[green]Successfully obtained client instance: {type(client_instance_for_tests)}[/green]")

        # Optional: Perform a simple API call to further test connection
        try:
            console.print("[grey50]Attempting simple model list check...[/grey50]")
            models_iterator = client_instance_for_tests.models.list()
            first_model = next(models_iterator, None)
            if first_model:
                 console.print(f"[green]✓ Connection check successful (found model: {first_model.name}).[/green]")
            else:
                 console.print("[yellow]Connection check completed, but no models listed.[/yellow]")
        except google_exceptions.GoogleAPIError as api_err:
            console.print(f"[bold yellow]Warning: Client obtained, but connection check failed with API error: {api_err}[/bold yellow]")
        except StopIteration:
             console.print("[yellow]Connection check completed, but no models listed.[/yellow]")
        except Exception as test_err:
             console.print(f"[bold yellow]Warning: Client obtained, but connection check failed with unexpected error: {test_err}[/bold yellow]")
             console.print(f"[grey50]{traceback.format_exc()}[/grey50]")

    except ValueError as e:
        console.print(f"[bold red]Test 1 Failed: Could not get client. Error: {e}[/bold red]")
        console.print("[yellow]Ensure the GEMINI_API_KEY environment variable is set correctly.[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Test 1 Failed with unexpected error: {e}[/bold red]")
        console.print(f"[grey50]{traceback.format_exc()}[/grey50]")

    # Test 2: List Available Models in a Table
    console.print("\n[yellow]Test 2: Listing available models...[/yellow]")
    if client_instance_for_tests: # Only proceed if client was obtained in Test 1
        try:
            models_iterator = client_instance_for_tests.models.list()

            # Create a table using Rich
            table = Table(title="Available Gemini Models", show_header=True, header_style="bold magenta", expand=True)
            table.add_column("Name", style="dim", width=30, overflow="fold")
            table.add_column("Display Name", style="cyan", width=30, overflow="fold")
            table.add_column("Version", style="green", width=10)
            table.add_column("Methods", style="blue", width=30, overflow="fold")
            table.add_column("Input Tokens", style="yellow", justify="right", width=12)
            table.add_column("Output Tokens", style="yellow", justify="right", width=12)
            # table.add_column("Description", style="white", overflow="fold") # Description can be very long

            model_count = 0
            for model in models_iterator:
                model_count += 1
                # Safely get attributes, providing defaults if missing (though unlikely for standard fields)
                name = getattr(model, 'name', 'N/A')
                display_name = getattr(model, 'display_name', 'N/A')
                version = getattr(model, 'version', 'N/A')
                methods = ", ".join(getattr(model, 'supported_generation_methods', []))
                input_limit = str(getattr(model, 'input_token_limit', 'N/A'))
                output_limit = str(getattr(model, 'output_token_limit', 'N/A'))
                # description = getattr(model, 'description', 'N/A')

                table.add_row(
                    name,
                    display_name,
                    version,
                    methods,
                    input_limit,
                    output_limit,
                    # description # Add description back if desired, but makes table wide
                )

            if model_count > 0:
                console.print(table)
                console.print(f"[green]✓ Successfully listed {model_count} models.[/green]")
            else:
                console.print("[yellow]API call successful, but no models were returned by the list operation.[/yellow]")

        except google_exceptions.GoogleAPIError as api_err:
            console.print(f"[bold red]Test 2 Failed: API Error listing models: {api_err}[/bold red]")
        except Exception as e:
            console.print(f"[bold red]Test 2 Failed: Unexpected error listing models: {e}[/bold red]")
            console.print(f"[grey50]{traceback.format_exc()}[/grey50]")
    else:
        console.print("[yellow]Skipping Test 2 because client initialization failed in Test 1.[/yellow]")


    # Test 3: Simulate Missing API Key
    console.print("\n[yellow]Test 3: Simulating missing API key...[/yellow]")
    original_api_key = os.environ.pop("GEMINI_API_KEY", None) # Temporarily remove key
    try:
        # Create a new manager instance to force re-loading attempt
        manager_no_key = GenAIClientManager(console=console)
        manager_no_key.get_client() # This should raise ValueError
        console.print("[bold red]Test 3 Failed: Expected ValueError was not raised.[/bold red]")
    except ValueError as e:
        console.print(f"[bold green]Test 3 Passed: ValueError raised as expected for missing key: {e}[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Test 3 Failed with unexpected error: {e}[/bold red]")
    finally:
        # Restore the API key if it was originally present
        if original_api_key:
            os.environ["GEMINI_API_KEY"] = original_api_key
            console.print("[grey50]Restored original API key environment variable.[/grey50]")

    console.print("\n[bold cyan]--- GenAIClientManager Testing Complete ---[/bold cyan]")
