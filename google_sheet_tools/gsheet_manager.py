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
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table

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
    
    def calculate_hash(self, data: pd.DataFrame) -> str:
        """
        Calculate hash from DataFrame consistently.
        
        Args:
            data: DataFrame to hash
        
        Returns:
            str: MD5 hash of the DataFrame
        """
        return hashlib.md5(data.to_csv(index=False).encode()).hexdigest()

    def download_worksheet(self, 
                      sheet_name: Optional[str] = None, 
                      sheet_index: int = 0,
                      spreadsheet_id: Optional[str] = None,
                      output_format: str = "csv",
                      output_dir: Optional[Path] = None,
                      filename: Optional[str] = None) -> Path:
        """
        Download worksheet data to a file and store metadata for change tracking.
        """
        # Get data as DataFrame
        df = self.get_worksheet_as_dataframe(sheet_name, sheet_index, spreadsheet_id)
        
        if df.empty:
            self.logger.warning("No data found in worksheet")
            return None
        
        # Get the hash from the raw data before any modifications
        current_hash = self.calculate_hash(df)
        
        # Fix ID column handling
        if "ID" in df.columns:
            df["ID"] = df["ID"].astype(str)
            df["ID"] = df["ID"].apply(lambda x: x.zfill(4) if len(x) < 4 else x)

        # Setup output directory
        if output_dir is None:
            output_dir = SPREADSHEET_SOURCE
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get worksheet name if needed
        if sheet_name is None:
            spreadsheet = self.open_spreadsheet(spreadsheet_id)
            sheet_name = spreadsheet.get_worksheet(sheet_index).title

        # Handle filename
        if filename is None:
            filename = sheet_name.replace(' ', '_').replace('/', '_')

        # Save file based on format
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
            raise ValueError(f"Unsupported output format: {output_format}")

        try:
            metadata = {
                "filename": output_path.name,
                "worksheet_name": sheet_name,
                "spreadsheet_id": spreadsheet_id,
                "download_time": datetime.now().isoformat(),
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": df.columns.tolist(),
                "data_hash": current_hash,  # Use the hash from Google Sheet
                "revision_id": str(int(time.time()))
            }
            
            # Save updated metadata
            prev_metadata_path = output_path.with_suffix('.meta.json')
            with open(prev_metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.logger.info(f"Updated metadata saved to {prev_metadata_path}")
            self.logger.info(f"Data saved to {output_path}")
            
        except Exception as e:
            self.logger.error(f"Error updating metadata: {str(e)}")

        return output_path
    
    def interactive_worksheet_download(self) -> None:
        """
        Interactive command-line interface for downloading worksheets.
        """
        console = Console()
        
        try:
            # Open spreadsheet and get worksheets
            spreadsheet = self.open_spreadsheet()
            worksheets = spreadsheet.worksheets()
            
            # Display available worksheets
            table = Table(title="📋 Available Worksheets")
            table.add_column("Index", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Rows", style="magenta")
            table.add_column("Columns", style="yellow")
            
            for idx, ws in enumerate(worksheets):
                table.add_row(
                    str(idx),
                    ws.title,
                    str(ws.row_count),
                    str(ws.col_count)
                )
            
            console.print(table)
            console.print()
            
            # Get user selection
            while True:
                try:
                    choice = Prompt.ask(
                        "Select worksheet by [cyan]index[/cyan] or [cyan]name[/cyan]",
                        default="0"
                    )
                    
                    # Try to get worksheet by index first
                    try:
                        idx = int(choice)
                        if 0 <= idx < len(worksheets):
                            selected_worksheet = worksheets[idx]
                            break
                    except ValueError:
                        # If not a number, try to find by name
                        matching_worksheets = [ws for ws in worksheets if ws.title.lower() == choice.lower()]
                        if matching_worksheets:
                            selected_worksheet = matching_worksheets[0]
                            break
                    
                    console.print("[red]Invalid selection. Please try again.[/red]")
                    
                except KeyboardInterrupt:
                    console.print("\n[yellow]Operation cancelled by user[/yellow]")
                    return
            
            # Show worksheet info and check for existing metadata
            output_path = SPREADSHEET_SOURCE / f"{selected_worksheet.title}.csv"
            meta_path = output_path.with_suffix('.meta.json')
            
            # Calculate hash using the same method
            current_data = pd.DataFrame(selected_worksheet.get_all_records())
            current_hash = self.calculate_hash(current_data)
            
            info_table = Table(title="📊 Worksheet Information", show_header=False)
            info_table.add_row("Title", selected_worksheet.title)
            info_table.add_row("Rows", str(selected_worksheet.row_count))
            info_table.add_row("Columns", str(selected_worksheet.col_count))
            info_table.add_row("Current Hash", current_hash)
            
            if meta_path.exists():
                with open(meta_path) as f:
                    metadata = json.load(f)
                    info_table.add_row("Last Download", metadata.get('download_time', 'Unknown'))
                    info_table.add_row("Local Hash", metadata.get('data_hash', 'Unknown'))
                    
                    if metadata.get('data_hash') != current_hash:
                        info_table.add_row("Status", "[red]Changes detected![/red]")
                    else:
                        info_table.add_row("Status", "[green]No changes[/green]")
            
            console.print(info_table)
            console.print()
            
            # Confirm download
            if Confirm.ask("Download this worksheet?"):
                self.download_worksheet(sheet_name=selected_worksheet.title)
                console.print("[green]✓ Download complete![/green]")
            else:
                console.print("[yellow]Download cancelled[/yellow]")
                
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            self.logger.error(f"Interactive download error: {str(e)}")


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