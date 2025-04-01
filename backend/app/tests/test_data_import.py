import pytest
import json
from pathlib import Path
from datetime import date
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ..models.admission import AdmissionModel, AdmissionCreate
from pydantic import ValidationError

console = Console()

class TestJsonValidation:
    """Test suite for validating JSON admission data files"""
    
    @pytest.fixture
    def json_data_path(self) -> Path:
        """Get path to JSON data files"""
        return Path("/home/gusmmm/Desktop/infoburn/data/output/json/admission_data")
    
    def test_json_structure(self, json_data_path):
        """Test that JSON files match expected model structure"""
        # Create table for results
        results_table = Table(
            "File", "Status", "Details",
            title="JSON Validation Results",
            show_lines=True
        )
        
        try:
            # Get all JSON files
            json_files = list(json_data_path.glob("*.json"))
            if not json_files:
                console.print(Panel(
                    "[yellow]No JSON files found in directory[/yellow]",
                    title="Warning"
                ))
                return
            
            for json_file in json_files:
                try:
                    # Load JSON data
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                    
                    # Validate against model
                    admission = AdmissionCreate(**data)
                    
                    # Verify date formats
                    date_fields = ['data_ent', 'data_alta', 'data_nasc']
                    for field in date_fields:
                        if value := getattr(admission, field):
                            assert isinstance(value, date), f"{field} is not a valid date"
                    
                    # Add success to table
                    results_table.add_row(
                        json_file.name,
                        "[green]Valid[/green]",
                        "✓ All fields validated successfully"
                    )
                    
                except ValidationError as e:
                    # Add validation error to table
                    results_table.add_row(
                        json_file.name,
                        "[red]Invalid[/red]",
                        f"✗ {str(e)}"
                    )
                except json.JSONDecodeError as e:
                    # Add JSON parsing error to table
                    results_table.add_row(
                        json_file.name,
                        "[red]Invalid JSON[/red]",
                        f"✗ {str(e)}"
                    )
                except Exception as e:
                    # Add unexpected error to table
                    results_table.add_row(
                        json_file.name,
                        "[red]Error[/red]",
                        f"✗ {str(e)}"
                    )
            
            # Display results
            console.print("\n")
            console.print(results_table)
            
        except Exception as e:
            console.print(f"[red]Error during testing: {str(e)}[/red]")
            raise

if __name__ == "__main__":
    pytest.main([__file__, "-v"])