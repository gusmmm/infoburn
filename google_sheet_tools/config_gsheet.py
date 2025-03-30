"""
Configuration management for environment variables and secrets.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from core_tools.key_manager import KeyManager

# Load environment variables from .env file
keyManager = KeyManager()
keyManager.validate_key("GOOGLE_SHEET_ID")
GOOGLE_SHEET_ID = keyManager.get_key("GOOGLE_SHEET_ID")

class Config:
    """Configuration values loaded from environment variables."""
    
    # Google Sheets settings
    GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
    
    @classmethod
    def get_sheet_id(cls) -> str:
        """Get the Google Sheet ID with validation."""
        if not cls.GOOGLE_SHEET_ID:
            raise ValueError("GOOGLE_SHEET_ID not set in environment variables")
        return cls.GOOGLE_SHEET_ID
    
    @classmethod
    def validate(cls) -> None:
        """Validate that all required configuration values are set."""
        missing = []
        
        if not cls.GOOGLE_SHEET_ID:
            missing.append("GOOGLE_SHEET_ID")
            
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}. "
                f"Please add them to your .env file at the root of the project."
            )
        
# test config_sheet class
if __name__ == "__main__":
    try:
        config = Config()
        config.validate()
        print("All required configuration values are set.")
    except ValueError as e:
        print(f"Configuration error: {e}")

    try:
        config.get_sheet_id()
        print(f"Google Sheet ID: {config.get_sheet_id()}")
    except ValueError as e:
        print(f"Error getting Google Sheet ID: {e}")
  