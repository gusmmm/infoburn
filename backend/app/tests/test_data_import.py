import pytest
import json
from pathlib import Path
from datetime import date
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress

from ..models.admission import AdmissionCreate
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
        results_table = Table(
            "File", 
            "Status", 
            "Details",
            title="JSON Validation Results",
            show_lines=True,
            title_style="bold magenta",
            header_style="bold cyan"
        )
        
        with Progress() as progress:
            task = progress.add_task("[cyan]Validating JSON files...", total=0)
            
            try:
                json_files = list(json_data_path.glob("*.json"))
                if not json_files:
                    console.print(Panel(
                        "[yellow]No JSON files found in directory[/yellow]",
                        title="Warning"
                    ))
                    return
                
                progress.update(task, total=len(json_files))
                
                for json_file in json_files:
                    try:
                        # Load and validate JSON
                        with open(json_file, 'r') as f:
                            data = json.load(f)
                        
                        admission = AdmissionCreate(**data)
                        
                        # Verify dates
                        for field in ['data_ent', 'data_alta', 'data_nasc']:
                            if value := getattr(admission, field, None):
                                assert isinstance(value, date)
                        
                        results_table.add_row(
                            json_file.name,
                            "[green]✓ Valid[/green]",
                            "All fields validated successfully"
                        )
                        
                    except ValidationError as e:
                        results_table.add_row(
                            json_file.name,
                            "[red]✗ Invalid[/red]",
                            str(e)
                        )
                    except json.JSONDecodeError as e:
                        results_table.add_row(
                            json_file.name,
                            "[red]✗ Invalid JSON[/red]",
                            str(e)
                        )
                    except Exception as e:
                        results_table.add_row(
                            json_file.name,
                            "[red]✗ Error[/red]",
                            str(e)
                        )
                    
                    progress.advance(task)
                
                # Display results
                console.print("\n")
                console.print(results_table)
                
            except Exception as e:
                console.print(f"[red]Error during testing: {str(e)}[/red]")
                raise

if __name__ == "__main__":
    pytest.main([__file__, "-v"])