"""
Google Sheets API Integration Module

This module provides a class-based interface for interacting with Google Sheets
using the gspread library. It handles authentication, data retrieval, and
file export operations.

Technical decisions:
- Class-based design for better encapsulation and state management
- Type hints for improved code clarity and IDE support
- Explicit error handling for better debugging
- Lazy initialization of connections to improve performance
- Configurable output formats and paths
"""
import sys
import os
import logging
import time
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
import pandas as pd
import json
import hashlib
from datetime import datetime


# Import project modules
from google_sheet_tools.config_gsheet import Config

# Third-party imports
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("GoogleSheetsClient")

# constants
CREDENTIALS = Path("credentials")
SPREADSHEET_SOURCE = Path("data/source/gsheets")

class GoogleSheetsClient:
    """
    Client for interacting with Google Sheets API.
    
    This class handles authentication, sheet operations, and data export
    functionality for Google Sheets integration.
    
    Attributes:
        credentials_file (Path): Path to the service account credentials file
        scopes (List[str]): OAuth scopes required for API access
        client (gspread.Client): Authenticated gspread client
    """
    
    def __init__(self, credentials_file: Optional[Union[str, Path]] = None) -> None:
        """
        Initialize the Google Sheets client with credentials.
        
        Args:
            credentials_file: Path to service account JSON file.
                             If None, uses default path from paths.CREDENTIALS.
        """
        # Set up logging
        self.logger = logger
        
        # Set credentials file path
        if credentials_file is None:
            self.credentials_file = CREDENTIALS / "credentials_gsheet.json"
        else:
            self.credentials_file = Path(credentials_file)
            
        # Define required API scopes
        self.scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/drive.metadata.readonly"
        ]
        
        # Initialize clients
        self._authenticate()
        
    def _authenticate(self) -> None:
        """
        Authenticate with Google APIs.
        """
        try:
            self.logger.info(f"Authenticating with credentials from: {self.credentials_file}")
            
            creds = Credentials.from_service_account_file(
                str(self.credentials_file),
                scopes=self.scopes
            )
            
            # Initialize gspread client
            self.client = gspread.authorize(creds)
            
            # Initialize Drive API client
            self.drive_service = build('drive', 'v3', credentials=creds)
            
            self.logger.info("Authentication successful")
            
        except FileNotFoundError:
            self.logger.error(f"Credentials file not found at {self.credentials_file}")
            raise FileNotFoundError(
                f"Credentials file not found at {self.credentials_file}. "
                "Please make sure the file exists in the credentials directory."
            )
        except Exception as e:
            self.logger.error(f"Authentication failed: {str(e)}")
            raise Exception(f"Authentication error: {str(e)}")
    
    def open_spreadsheet(self, spreadsheet_id: Optional[str] = None) -> gspread.Spreadsheet:
        """
        Open a Google Spreadsheet by its ID.
        
        Args:
            spreadsheet_id: The ID from the spreadsheet URL.
                           If None, uses the ID from Config.
                           
        Returns:
            gspread.Spreadsheet: The opened spreadsheet object
            
        Raises:
            ValueError: If spreadsheet_id is not provided and not in Config
            Exception: For spreadsheet access errors
        """
        try:
            # Use provided ID or get from environment
            if spreadsheet_id is None:
                spreadsheet_id = Config.get_sheet_id()
                self.logger.info(f"Using spreadsheet ID from environment: {spreadsheet_id}")
            
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            self.logger.info(f"Opened spreadsheet: '{spreadsheet.title}'")
            
            return spreadsheet
            
        except Exception as e:
            self.logger.error(f"Error opening spreadsheet: {str(e)}")
            raise
    
    def list_worksheets(self, spreadsheet_id: Optional[str] = None) -> List[str]:
        """
        List all worksheets in a spreadsheet.
        
        Args:
            spreadsheet_id: The ID from the spreadsheet URL.
                           If None, uses the ID from Config.
                           
        Returns:
            List[str]: List of worksheet titles
        """
        spreadsheet = self.open_spreadsheet(spreadsheet_id)
        worksheets = [sheet.title for sheet in spreadsheet.worksheets()]
        
        self.logger.info(f"Found {len(worksheets)} worksheets: {', '.join(worksheets)}")
        return worksheets
    
    def get_worksheet_data(self, 
                          sheet_name: Optional[str] = None, 
                          sheet_index: int = 0,
                          spreadsheet_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get data from a specific worksheet as a list of dictionaries.
        
        Args:
            sheet_name: Name of the worksheet to access
            sheet_index: Index of the worksheet if name not provided (default: 0)
            spreadsheet_id: The spreadsheet ID (if None, uses Config value)
            
        Returns:
            List[Dict[str, Any]]: List of rows as dictionaries with column headers as keys
            
        Raises:
            gspread.exceptions.WorksheetNotFound: If sheet_name doesn't exist
            IndexError: If sheet_index is out of range
        """
        spreadsheet = self.open_spreadsheet(spreadsheet_id)
        
        # Get the specified worksheet
        try:
            if sheet_name:
                worksheet = spreadsheet.worksheet(sheet_name)
                self.logger.info(f"Accessed worksheet '{sheet_name}'")
            else:
                worksheet = spreadsheet.get_worksheet(sheet_index)
                self.logger.info(f"Accessed worksheet at index {sheet_index}: '{worksheet.title}'")
        
            # Get all records (list of dictionaries)
            data = worksheet.get_all_records()
            self.logger.info(f"Retrieved {len(data)} rows of data")
            
            return data
            
        except gspread.exceptions.WorksheetNotFound:
            self.logger.error(f"Worksheet '{sheet_name}' not found")
            raise
        except IndexError:
            self.logger.error(f"Worksheet index {sheet_index} is out of range")
            raise
    
    def get_worksheet_as_dataframe(self, 
                                  sheet_name: Optional[str] = None, 
                                  sheet_index: int = 0,
                                  spreadsheet_id: Optional[str] = None) -> pd.DataFrame:
        """
        Get worksheet data as a pandas DataFrame.
        
        Args:
            sheet_name: Name of the worksheet to access
            sheet_index: Index of the worksheet if name not provided (default: 0)
            spreadsheet_id: The spreadsheet ID (if None, uses Config value)
            
        Returns:
            pandas.DataFrame: DataFrame containing the worksheet data
        """
        data = self.get_worksheet_data(sheet_name, sheet_index, spreadsheet_id)
        return pd.DataFrame(data)
    
    def download_worksheet(self, 
                  sheet_name: Optional[str] = None, 
                  sheet_index: int = 0,
                  spreadsheet_id: Optional[str] = None,
                  output_format: str = "csv",
                  output_dir: Optional[Path] = None,
                  filename: Optional[str] = None) -> Path:
        """
        Download worksheet data to a file and store metadata for change tracking.
        
        Args:
            sheet_name: Name of the worksheet to access
            sheet_index: Index of the worksheet if name not provided (default: 0)
            spreadsheet_id: The spreadsheet ID (if None, uses Config value)
            output_format: Format to save data as ("csv", "excel", "json")
            output_dir: Directory to save the file (if None, uses SPREADSHEET_SOURCE)
            filename: Custom filename to use (if None, uses worksheet name)
            
        Returns:
            Path: Path to the saved file
        """
        # Get data as DataFrame
        df = self.get_worksheet_as_dataframe(sheet_name, sheet_index, spreadsheet_id)
        
        if df.empty:
            self.logger.warning("No data found in worksheet")
            return None
        
        # Fix only the exact "ID" column to preserve leading zeros (not all columns containing "ID")
        if "ID" in df.columns:
            # Convert ID column to string type
            df["ID"] = df["ID"].astype(str)
            
            # if ID value only has 3 digits, add one leading zero
            df["ID"] = df["ID"].apply(lambda x: x.zfill(4) if len(x) < 4 else x)
            # Ensure the ID column is treated as a string to preserve leading zeros
            # This is important for IDs like "0025" to remain "0025" in the output

        # Determine output directory
        if output_dir is None:
            output_dir = SPREADSHEET_SOURCE  # Use the constant defined at the top level
    
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get worksheet name if not specified (for filename)
        if sheet_name is None:
            spreadsheet = self.open_spreadsheet(spreadsheet_id)
            sheet_name = spreadsheet.get_worksheet(sheet_index).title
    
        # Use custom filename or create one from sheet name
        if filename is None:
            # Sanitize sheet name for filename
            filename = sheet_name.replace(' ', '_').replace('/', '_')
    
        # Construct full output path with appropriate extension
        if output_format.lower() == "csv":
            output_path = output_dir / f"{filename}.csv"
            df.to_csv(output_path, index=False)
        elif output_format.lower() == "excel":
            output_path = output_dir / f"{filename}.xlsx"
            df.to_excel(output_path, index=False)
        elif output_format.lower() == "json":
            output_path = output_dir / f"{filename}.json"
            df.to_json(output_path, orient='records', indent=2)
        else:
            raise ValueError(f"Unsupported output format: {output_format}. "
                            "Supported formats: csv, excel, json")
        
        # Create metadata with focus on data hash and revision tracking
        try:
            # Calculate data fingerprint
            data_hash = hashlib.md5(df.to_csv().encode()).hexdigest()
            
            # Create metadata
            metadata = {
                "filename": output_path.name,
                "worksheet_name": sheet_name,
                "spreadsheet_id": spreadsheet_id,
                "download_time": datetime.now().isoformat(),
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": df.columns.tolist(),
                "data_hash": data_hash,
                "revision_id": str(int(time.time())),
            }
        except Exception as e:
            self.logger.error(f"Error creating metadata: {str(e)}")
            metadata = {}  # Use empty metadata as fallback
    
        # Check if previous metadata exists to preserve revision info
        prev_metadata_path = output_path.with_suffix('.meta.json')
        if prev_metadata_path.exists():
            try:
                with open(prev_metadata_path, 'r') as f:
                    prev_metadata = json.load(f)
                    # If hash is the same, keep the previous revision ID
                    if prev_metadata.get('data_hash') == data_hash:
                        metadata['revision_id'] = prev_metadata.get('revision_id', metadata['revision_id'])
                    else:
                        # If content changed, increment the revision ID
                        try:
                            old_rev = int(prev_metadata.get('revision_id', '0'))
                            metadata['revision_id'] = str(old_rev + 1)
                        except:
                            # If revision ID isn't numeric, use timestamp
                            pass
            except:
                pass
        
        # Save metadata alongside the data file
        metadata_path = output_path.with_suffix('.meta.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        self.logger.info(f"Metadata saved to {metadata_path}")
        # Log the download
        self.logger.info(f"Data saved to {output_path}")
        return output_path
        
    def download_all_worksheets(self, 
                               spreadsheet_id: Optional[str] = None,
                               output_format: str = "csv") -> Dict[str, Path]:
        """
        Download all worksheets from a spreadsheet.
        
        Args:
            spreadsheet_id: The spreadsheet ID (if None, uses Config value)
            output_format: File format - "csv", "excel", or "json" (default: "csv")
            
        Returns:
            Dict[str, Path]: Dictionary mapping worksheet names to output file paths
        """
        # Get list of all worksheets
        worksheet_names = self.list_worksheets(spreadsheet_id)
        
        # Download each worksheet
        results = {}
        for name in worksheet_names:
            try:
                output_path = self.download_worksheet(
                    sheet_name=name,
                    spreadsheet_id=spreadsheet_id,
                    output_format=output_format
                )
                results[name] = output_path
            except Exception as e:
                self.logger.error(f"Error downloading worksheet '{name}': {str(e)}")
                # Continue with other worksheets even if one fails
        
        return results

    def interactive_worksheet_download(self, 
                                      spreadsheet_id: Optional[str] = None,
                                      output_format: str = "csv") -> Optional[Path]:
        """
        Interactive interface for selecting and downloading worksheets.
        
        This method guides the user through:
        1. Connecting to the Google spreadsheet
        2. Listing available worksheets
        3. Selecting which worksheet to work with
        4. Displaying metadata about the current sheet and local file
        5. Letting user decide whether to download
        
        Args:
            spreadsheet_id: ID of the spreadsheet (if None, uses Config)
            output_format: Format to save data in ("csv", "excel", or "json")
            
        Returns:
            Path: Path to the downloaded file if successful, otherwise None
        """
        try:
            # Connect to spreadsheet
            self.logger.info("Connecting to Google Spreadsheet...")
            spreadsheet = self.open_spreadsheet(spreadsheet_id)
            print(f"\n📊 Connected to: '{spreadsheet.title}'")
            
            # Get available worksheets
            worksheet_names = self.list_worksheets(spreadsheet_id)
            if not worksheet_names:
                print("❌ No worksheets found in this spreadsheet.")
                return None
            
            # Display worksheet selection menu
            print("\n🔍 Available worksheets:")
            for i, name in enumerate(worksheet_names, 1):
                print(f"  {i}. {name}")
            
            # Get user selection
            while True:
                try:
                    selection = input("\n👉 Enter worksheet number to download: ")
                    index = int(selection) - 1
                    if 0 <= index < len(worksheet_names):
                        selected_worksheet = worksheet_names[index]
                        break
                    else:
                        print(f"❌ Please enter a number between 1 and {len(worksheet_names)}")
                except ValueError:
                    print("❌ Please enter a valid number")
            
            print(f"\n✅ Selected: '{selected_worksheet}'")
            
            # Determine output path
            filename = selected_worksheet.replace(' ', '_').replace('/', '_')
            output_path = SPREADSHEET_SOURCE / f"{filename}.{output_format}"
            
            # Check if file already exists
            file_exists = output_path.exists()
            
            if file_exists:
                print(f"\n🔄 Found existing file: {output_path}")
            else:
                print("\n🆕 No existing file found. Will be a first download.")
            
            # Display metadata and ask for confirmation
            should_download = self._check_for_updates(output_path, selected_worksheet, spreadsheet_id)
            
            # Download if needed
            if should_download:
                print(f"\n⬇️ Downloading '{selected_worksheet}' to {output_path}")
                result_path = self.download_worksheet(
                    sheet_name=selected_worksheet,
                    spreadsheet_id=spreadsheet_id,
                    output_format=output_format,
                    filename=filename
                )
                print(f"✅ Download complete: {result_path}")
                return result_path
            else:
                print("\n⏭️ Skipping download as requested.")
                return output_path if file_exists else None
                
        except Exception as e:
            self.logger.error(f"Error in interactive download: {str(e)}")
            print(f"\n❌ Error: {str(e)}")
            return None
            
    def _check_for_updates(self, 
                          file_path: Path, 
                          worksheet_name: str,
                          spreadsheet_id: Optional[str] = None) -> bool:
        """
        Display metadata focusing on revision ID comparison.
        
        Shows revision IDs from both local metadata and the current sheet,
        letting the user decide whether to download based on this comparison.
        
        Args:
            file_path: Path to the local CSV file
            worksheet_name: Name of the worksheet to compare
            spreadsheet_id: ID of the spreadsheet (if None, uses Config)
            
        Returns:
            bool: True if user wants to download, False otherwise
        """
        self.logger.info(f"Checking revision info for {file_path} and {worksheet_name}")
        
        # Check for metadata file
        metadata_path = file_path.with_suffix('.meta.json')
        local_metadata_exists = metadata_path.exists()
        
        try:
            # Get spreadsheet info using gspread
            spreadsheet = self.open_spreadsheet(spreadsheet_id)
            worksheet = spreadsheet.worksheet(worksheet_name)
            
            # Get current data and calculate hash
            current_data = self.get_worksheet_data(worksheet_name, spreadsheet_id)
            current_df = pd.DataFrame(current_data)
            current_hash = hashlib.md5(current_df.to_csv().encode()).hexdigest()
            
            print("\n📋 Google Sheet Info:")
            print(f"   - Spreadsheet title: {spreadsheet.title}")
            print(f"   - Worksheet: {worksheet.title}")
            print(f"   - Current row count: {len(current_data)}")
            print(f"   - Current column count: {len(current_df.columns) if not current_df.empty else 0}")
            print(f"   - Current data hash: {current_hash}")
            
            # If we have local metadata, display it for comparison
            if local_metadata_exists:
                try:
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    
                    print("\n📄 Local File Metadata:")
                    print(f"   - Downloaded on: {metadata.get('download_time', 'Unknown')}")
                    
                    # Display revision IDs for comparison
                    local_revision_id = metadata.get('revision_id', 'Unknown')
                    print(f"   - Local revision ID: {local_revision_id}")
                    
                    # Display previous hash
                    local_hash = metadata.get('data_hash', 'Unknown')
                    print(f"   - Local data hash: {local_hash}")
                    
                    # Compare hashes to detect content changes
                    if local_hash != current_hash:
                        print("\n⚠️ Data content has changed since last download!")
                    else:
                        print("\n✅ Data content appears to be identical")
                        
                    # Display row count comparison
                    local_row_count = metadata.get('row_count', 0)
                    if local_row_count != len(current_data):
                        print(f"⚠️ Row count changed: {local_row_count} → {len(current_data)}")
                        
                except Exception as e:
                    print(f"\n⚠️ Error reading local metadata: {str(e)}")
            else:
                print("\n📝 No local metadata found - this would be a first-time download.")
                
            # Let the user decide
            default = not local_metadata_exists  # Default to Yes for new files, No for existing ones
            return self._prompt_download_confirmation(default=default)
                
        except Exception as e:
            self.logger.error(f"Error fetching worksheet info: {str(e)}")
            print(f"\n⚠️ Error fetching worksheet info: {str(e)}")
            return self._prompt_download_confirmation()
            
    def _prompt_download_confirmation(self, default: bool = True) -> bool:
        """
        Ask user to confirm download.
        
        Args:
            default: Default answer if user just presses Enter
            
        Returns:
            bool: True if user confirms, False otherwise
        """
        default_text = "Y/n" if default else "y/N"
        while True:
            response = input(f"\n❓ Download/update the file? [{default_text}]: ").strip().lower()
            
            if not response:  # Empty response, use default
                return default
                
            if response in ('y', 'yes'):
                return True
            elif response in ('n', 'no'):
                return False
            else:
                print("Please answer with 'y' or 'n'")
    
       
    def get_file_revision_info(self, file_id: str) -> Dict[str, Any]:
        """
        Get revision information for a Google Drive file.
        
        Args:
            file_id: The ID of the file (spreadsheet)
            
        Returns:
            Dict with revision information
        """
        try:
            # Get file metadata from Drive API
            file_metadata = self.drive_service.files().get(
                fileId=file_id, 
                fields="id,name,mimeType,modifiedTime,version"
            ).execute()
            
            # Get list of revisions
            revisions = self.drive_service.revisions().list(
                fileId=file_id,
                fields="revisions(id,modifiedTime,lastModifyingUser)"
            ).execute()
            
            # Get the latest revision
            latest_revision = None
            if 'revisions' in revisions:
                latest_revision = revisions['revisions'][-1] if revisions['revisions'] else None
                
            # Combine information
            result = {
                'file_id': file_id,
                'name': file_metadata.get('name'),
                'modified_time': file_metadata.get('modifiedTime'),
                'version': file_metadata.get('version', '0'),
                'latest_revision_id': latest_revision.get('id') if latest_revision else None,
                'latest_revision_time': latest_revision.get('modifiedTime') if latest_revision else None,
            }
            
            return result
        except Exception as e:
            self.logger.error(f"Error getting file revision info: {str(e)}")
            raise


def main():
    """
    Example usage when script is run directly.
    """
    try:
        # Load environment variables
        from core_tools.key_manager import KeyManager

        # Load environment variables from .env file
        keyManager = KeyManager()
        keyManager.validate_key("GOOGLE_SHEET_ID")
        GOOGLE_SHEET_ID = keyManager.get_key("GOOGLE_SHEET_ID")
        
        # Initialize client
        gs_client = GoogleSheetsClient()
        
        # Use the interactive function
        print("\n🌟 Interactive Google Sheets Downloader 🌟\n")
        gs_client.interactive_worksheet_download()
            
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()