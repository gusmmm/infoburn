"""
Configuration settings for the markdown anonymizer.
"""

import os
from pathlib import Path
from typing import Dict, Any

class AnonymizerConfig:
    """
    Configuration settings manager for the markdown anonymizer.
    """
    
    def __init__(self, config_file: str = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_file: Optional path to a JSON configuration file
        """
        self.config: Dict[str, Any] = {
            # Default configuration settings
            "date_formats": ["%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d %b %Y", "%d de %B de %Y"],
            "entity_types": {
                "patient_names": "patient",
                "addresses": "address",
                "phone_numbers": "phone",
                "id_numbers": "id",
                "doctor_names": "doctor",
                "hospital_names": "hospital"
            },
            "min_year": 2005,
            "api_timeout": 30,  # seconds
            "batch_size": 5,  # files processed in parallel
            "model_name": "gemini-pro",
            "max_prompt_length": 4000,
        }
        
        # Load config from file if provided
        if config_file and os.path.exists(config_file):
            import json
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.config.update(json.load(f))
            except Exception as e:
                print(f"Error loading config file: {e}")

    def get(self, key: str, default=None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key doesn't exist
            
        Returns:
            Configuration value
        """
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key
            value: Value to set
        """
        self.config[key] = value

    def save(self, config_file: str) -> bool:
        """
        Save current configuration to file.
        
        Args:
            config_file: Path to save the configuration
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(self.config, f, indent=2)
            return True
        except Exception:
            return False