from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from quality_control_tools.id import IDQualityControl
from quality_control_tools.data_nasc import BirthDateQualityControl
from quality_control_tools.data_ent import DateEntQualityControl
from quality_control_tools.data_alta import DateComparisonQualityControl
from quality_control_tools.origem_destino import OrigemDestinoQualityControl
from quality_control_tools.processo import ProcessoQualityControl

def display_menu(console: Console) -> None:
    """
    Display the main menu for quality control tools.
    
    Args:
        console: Rich console for formatted output
    """
    console.print(Panel.fit(
        "[bold cyan]Burns Critical Care Unit Quality Control Tools[/bold cyan]",
        title="Main Menu"))
    
    # Create menu table
    table = Table(show_header=False, box=None)
    table.add_column("Option", style="cyan")
    table.add_column("Description", style="white")
    
    table.add_row("[1]", "Patient ID Quality Control")
    table.add_row("[2]", "Birth Date Quality Control")
    table.add_row("[3]", "Admission Date Quality Control")
    table.add_row("[4]", "Discharge Date Quality Control")
    table.add_row("[5]", "Origin/Destination Quality Control")
    table.add_row("[6]", "Process Number Quality Control")
    table.add_row("[7]", "Run All Quality Controls")
    table.add_row("[8]", "Exit")
    
    console.print(table)
    console.print()

def get_filename(console: Console, default_file: str = "Doentes_typed.csv") -> str:
    """
    Get filename from user or use default.
    
    Args:
        console: Rich console for formatted output
        default_file: Default filename to use
        
    Returns:
        str: Selected filename
    """
    console.print("[bold]File Selection:[/bold]")
    console.print(f"[1] Use default file ({default_file})")
    console.print("[2] Specify different file")
    
    choice = input("\nEnter choice [1-2]: ")
    
    if choice == "2":
        return input("Enter CSV filename: ")
    return default_file

def run_all_checks(filename: str, console: Console) -> None:
    """
    Run all quality control checks sequentially.
    
    Args:
        filename: Name of the CSV file to analyze
        console: Rich console for formatted output
    """
    try:
        console.print(Panel.fit(
            "[bold blue]Running All Quality Control Checks[/bold blue]"))
        
        # Run each quality control module
        console.print("\n[bold]1. ID Quality Control[/bold]")
        id_qc = IDQualityControl(filename)
        id_qc.run_all_checks()
        
        console.print("\n[bold]2. Birth Date Quality Control[/bold]")
        birth_qc = BirthDateQualityControl(filename)
        birth_qc.run_all_checks()
        
        console.print("\n[bold]3. Admission Date Quality Control[/bold]")
        admission_qc = DateEntQualityControl(filename)
        admission_qc.run_all_checks()
        
        console.print("\n[bold]4. Discharge Date Quality Control[/bold]")
        discharge_qc = DateComparisonQualityControl(filename)
        discharge_qc.run_all_checks()
        
        console.print("\n[bold]5. Origin/Destination Quality Control[/bold]")
        od_qc = OrigemDestinoQualityControl(filename)
        od_qc.run_all_checks()
        
        console.print("\n[bold]6. Process Number Quality Control[/bold]")
        processo_qc = ProcessoQualityControl(filename)
        processo_qc.run_all_checks()
        
        console.print("\n[green]All quality control checks completed![/green]")
        
    except Exception as e:
        console.print(f"[red]Error during quality control checks: {str(e)}[/red]")
        import traceback
        console.print(traceback.format_exc())

def main():
    """
    Main function providing a menu interface to all quality control tools.
    """
    try:
        console = Console()
        
        while True:
            display_menu(console)
            choice = input("Enter choice [1-8]: ")
            
            if choice == "8":
                console.print("[yellow]Exiting program[/yellow]")
                break
                
            if choice not in ["1", "2", "3", "4", "5", "6", "7"]:
                console.print("[red]Invalid choice. Please try again.[/red]")
                continue
                
            # Get filename
            filename = get_filename(console)
            
            try:
                if choice == "1":
                    id_qc = IDQualityControl(filename)
                    id_qc.run_all_checks()
                    
                elif choice == "2":
                    birth_qc = BirthDateQualityControl(filename)
                    birth_qc.run_all_checks()
                    
                elif choice == "3":
                    admission_qc = DateEntQualityControl(filename)
                    admission_qc.run_all_checks()
                    
                elif choice == "4":
                    discharge_qc = DateComparisonQualityControl(filename)
                    discharge_qc.run_all_checks()
                    
                elif choice == "5":
                    od_qc = OrigemDestinoQualityControl(filename)
                    od_qc.run_all_checks()
                    
                elif choice == "6":
                    processo_qc = ProcessoQualityControl(filename)
                    processo_qc.run_all_checks()
                    
                elif choice == "7":
                    run_all_checks(filename, console)
                    
                # Wait for user input before showing menu again
                input("\nPress Enter to continue...")
                
            except Exception as e:
                console.print(f"[red]Error: {str(e)}[/red]")
                import traceback
                console.print(traceback.format_exc())
                input("\nPress Enter to continue...")
                
    except KeyboardInterrupt:
        console.print("\n[yellow]Program terminated by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Unexpected error: {str(e)}[/red]")
        import traceback
        console.print(traceback.format_exc())

if __name__ == "__main__":
    main()