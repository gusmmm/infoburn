import os
from dotenv import load_dotenv
from rich import print

class KeyManager:
    """
    Manages the retrieval of keys from environment variables, providing a consistent
    interface for accessing configuration settings.
    """

    def __init__(self, dotenv_path=".env"):
        """
        Initializes the KeyManager with the path to the .env file.

        Args:
            dotenv_path (str, optional): The path to the .env file. Defaults to ".env".
        """
        self.dotenv_path = dotenv_path
        try:
            load_dotenv(dotenv_path=self.dotenv_path)
        except FileNotFoundError:
            print(f"[red]Error: .env file not found at {self.dotenv_path}[/red]")
            raise
        except OSError as e:
            print(f"[red]Error: Could not read .env file: {e}[/red]")
            raise

    def get_key(self, key_name: str) -> str:
        """
        Retrieves the value of a specified key from the environment variables.

        Args:
            key_name (str): The name of the key to retrieve.

        Returns:
            str: The value of the key if found.

        Raises:
            ValueError: If the key is not found in the environment variables.
        """
        key_value = os.environ.get(key_name)
        if key_value is None:
            raise ValueError(f"Key '{key_name}' not found in environment variables.")
        return key_value

    def validate_key(self, key_name: str):
        """
        Validates that a key exists in the environment variables.

        Args:
            key_name (str): The name of the key to validate.

        Raises:
            ValueError: If the key is not found in the environment variables.
        """
        if key_name not in os.environ:
            raise ValueError(f"Key '{key_name}' not found in environment variables.")
        
# test the KeyManager class
if __name__ == "__main__":
    key_manager = KeyManager()
    try:
        key_manager.validate_key("GEMINI_API_KEY")
        print(key_manager.get_key("GEMINI_API_KEY"))
    except ValueError as e:
        print(f"[red]Error: {e}[/red]")