"""
Terminal Menu System Module

This module provides a flexible, extensible terminal menu system for the InfoBurn application.
It creates a user-friendly interface for navigating between different application features
using the Rich library for enhanced terminal output.

Technical decisions:
- Class-based architecture for modular menu management
- Dynamic menu registration system for extensibility
- Rich library integration for enhanced visual feedback
- Type hints for improved code clarity and IDE support
- Encapsulation of menu display and navigation logic
"""

import sys
from typing import Dict, List, Callable, Optional, Any, Union
from pathlib import Path

# Third-party imports
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt, IntPrompt

class MenuOption:
    """
    Represents a single menu option with associated functionality.
    
    Attributes:
        name (str): Display name of the menu option
        callback (Callable): Function to call when option is selected
        description (str): Detailed description of what the option does
        is_exit (bool): Whether selecting this option should exit the current menu
    """
    
    def __init__(self, 
                name: str, 
                callback: Callable, 
                description: str = "", 
                is_exit: bool = False) -> None:
        """
        Initialize a menu option.
        
        Args:
            name: Display name of the option
            callback: Function to execute when option is selected
            description: Detailed explanation of the option's functionality
            is_exit: Whether this option exits the menu
        """
        self.name = name
        self.callback = callback
        self.description = description
        self.is_exit = is_exit
        
    def execute(self, **kwargs: Any) -> Any:
        """
        Execute the callback function associated with this option.
        
        Args:
            **kwargs: Additional parameters to pass to the callback
            
        Returns:
            Any: Result from the callback function
        """
        return self.callback(**kwargs)

class Menu:
    """
    Manages a set of menu options and handles user interaction.
    
    This class represents a menu with multiple selectable options,
    handling display, user input, and option execution.
    
    Attributes:
        title (str): Title of the menu
        options (List[MenuOption]): List of available options
        console (rich.console.Console): Rich console for enhanced display
        parent_menu (Optional['Menu']): Parent menu to return to
        show_back_option (bool): Whether to show an option to return to parent menu
    """
    
    def __init__(self, 
                title: str, 
                console: Optional[Console] = None,
                parent_menu: Optional['Menu'] = None) -> None:
        """
        Initialize a menu with a title.
        
        Args:
            title: Title of the menu
            console: Rich console instance for display (creates new one if None)
            parent_menu: Parent menu to return to (if any)
        """
        self.title = title
        self.options: List[MenuOption] = []
        self.console = console if console else Console()
        self.parent_menu = parent_menu
        self.show_back_option = parent_menu is not None
        
    def add_option(self, 
                  name: str, 
                  callback: Callable, 
                  description: str = "", 
                  is_exit: bool = False) -> 'Menu':
        """
        Add a new option to the menu.
        
        Args:
            name: Display name of the option
            callback: Function to execute when option is selected
            description: Detailed explanation of the option's functionality
            is_exit: Whether this option exits the menu
            
        Returns:
            Menu: Self reference for method chaining
        """
        option = MenuOption(name, callback, description, is_exit)
        self.options.append(option)
        return self
    
    def add_submenu(self, title: str) -> 'Menu':
        """
        Create and add a submenu to this menu.
        
        Args:
            title: Title of the submenu
            
        Returns:
            Menu: The newly created submenu
        """
        submenu = Menu(title, console=self.console, parent_menu=self)
        
        # Add the submenu as an option in this menu
        def open_submenu(**kwargs: Any) -> None:
            submenu.display()
            
        self.add_option(title, open_submenu, f"Open {title} submenu")
        return submenu
    
    def add_exit_option(self, name: str = "Exit", description: str = "Exit the current menu") -> 'Menu':
        """
        Add an exit option to the menu.
        
        Args:
            name: Display name for the exit option
            description: Description of the exit option
            
        Returns:
            Menu: Self reference for method chaining
        """
        def exit_function(**kwargs: Any) -> bool:
            return True
            
        self.add_option(name, exit_function, description, is_exit=True)
        return self
    
    def add_back_option(self, 
                       name: str = "Back", 
                       description: str = "Return to previous menu") -> 'Menu':
        """
        Add a back option that returns to the parent menu.
        
        Args:
            name: Display name for the back option
            description: Description of the back option
            
        Returns:
            Menu: Self reference for method chaining
        """
        if self.parent_menu:
            def back_function(**kwargs: Any) -> bool:
                self.parent_menu.display()
                return True
                
            self.add_option(name, back_function, description, is_exit=True)
        return self
    
    def _display_header(self) -> None:
        """
        Display the menu header with title.
        """
        self.console.print()
        self.console.print(Panel(
            Text(self.title, justify="center", style="bold cyan"),
            border_style="cyan"
        ))
        self.console.print()
    
    def _display_options(self) -> Table:
        """
        Format and display the menu options.
        
        Returns:
            rich.table.Table: Table containing formatted menu options
        """
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Number", style="bold green", justify="right")
        table.add_column("Option", style="yellow")
        table.add_column("Description", style="dim")
        
        for i, option in enumerate(self.options, 1):
            name_style = "bold red" if option.is_exit else "yellow"
            table.add_row(
                f"[{i}]", 
                f"[{name_style}]{option.name}[/{name_style}]", 
                option.description
            )
            
        return table
    
    def _get_user_choice(self) -> int:
        """
        Get the user's menu choice.
        
        Returns:
            int: Index of the selected option (1-based)
        """
        while True:
            try:
                choice = IntPrompt.ask("\n[bold green]Enter your choice[/bold green]", 
                                       console=self.console)
                
                if 1 <= choice <= len(self.options):
                    return choice
                else:
                    self.console.print(f"[bold red]Invalid choice. Please enter a number between 1 and {len(self.options)}.[/bold red]")
            except KeyboardInterrupt:
                # Handle Ctrl+C gracefully
                self.console.print("\n[bold red]Operation cancelled by user.[/bold red]")
                sys.exit(0)
            except ValueError:
                self.console.print("[bold red]Please enter a valid number.[/bold red]")
    
    def display(self, **kwargs: Any) -> None:
        """
        Display the menu and handle user interaction.
        
        Args:
            **kwargs: Additional parameters to pass to the option callbacks
        """
        while True:
            # Clear screen for better UX
            self.console.clear()
            
            # Display menu header and options
            self._display_header()
            table = self._display_options()
            self.console.print(table)
            
            # Get user choice and execute the selected option
            choice = self._get_user_choice()
            selected_option = self.options[choice - 1]
            
            # Clear the screen before executing the option
            self.console.clear()
            
            # Execute the selected option
            result = selected_option.execute(**kwargs)
            
            # If option is marked as exit, break the loop
            if selected_option.is_exit:
                break
            
            # Pause after executing the option
            if not selected_option.is_exit:
                self.console.print("\n[bold cyan]Press Enter to return to the menu...[/bold cyan]")
                input()


class MenuManager:
    """
    Central manager for all application menus.
    
    This class serves as a registry and factory for application menus,
    providing access to registered menus by name.
    
    Attributes:
        console (rich.console.Console): Shared console for all menus
        menus (Dict[str, Menu]): Dictionary of registered menus by name
        main_menu (Menu): Reference to the main application menu
    """
    
    def __init__(self) -> None:
        """
        Initialize the menu manager with a main menu.
        """
        self.console = Console()
        self.menus: Dict[str, Menu] = {}
        self.main_menu = self.create_menu("InfoBurn Terminal Interface")
        
    def create_menu(self, 
                   title: str, 
                   parent_menu_name: Optional[str] = None) -> Menu:
        """
        Create a new menu and register it.
        
        Args:
            title: Title of the menu
            parent_menu_name: Name of the parent menu (if any)
            
        Returns:
            Menu: The newly created menu
        """
        # Get the parent menu if specified
        parent_menu = self.menus.get(parent_menu_name) if parent_menu_name else None
        
        # Create the new menu
        menu = Menu(title, console=self.console, parent_menu=parent_menu)
        
        # Register the menu
        self.menus[title] = menu
        
        return menu
    
    def get_menu(self, title: str) -> Optional[Menu]:
        """
        Get a registered menu by title.
        
        Args:
            title: Title of the menu to retrieve
            
        Returns:
            Optional[Menu]: The requested menu or None if not found
        """
        return self.menus.get(title)
    
    def run(self) -> None:
        """
        Run the main application menu.
        """
        try:
            self.main_menu.display()
        except KeyboardInterrupt:
            self.console.print("\n[bold red]Application terminated by user.[/bold red]")
            sys.exit(0)
        except Exception as e:
            self.console.print(f"\n[bold red]Error: {str(e)}[/bold red]")
            sys.exit(1)


def setup_menus() -> MenuManager:
    """
    Set up the application menu structure.
    
    This function creates and configures all application menus.
    
    Returns:
        MenuManager: Configured menu manager with all menus
    """
    # Create menu manager
    manager = MenuManager()
    
    # Add options to main menu
    main_menu = manager.main_menu
    
    # Add Google Sheets menu option
    def launch_google_sheets_interactive():
        from google_sheet_tools.gsheet_manager import GoogleSheetsClient
        try:
            gs_client = GoogleSheetsClient()
            gs_client.interactive_worksheet_download()
        except Exception as e:
            manager.console.print(f"[bold red]Error: {str(e)}[/bold red]")
    
    main_menu.add_option(
        "Google Sheets Data Management", 
        launch_google_sheets_interactive,
        "Download and manage data from Google Sheets"
    )
    
    # Add CSV Typing option
    def launch_csv_typer():
        from google_sheet_tools.csv_typer import main as csv_typer_main
        try:
            csv_typer_main()
        except Exception as e:
            manager.console.print(f"[bold red]Error in CSV Typer: {str(e)}[/bold red]")
    
    main_menu.add_option(
        "Type CSV Data", 
        launch_csv_typer,
        "Convert and validate CSV data types"
    )
    
    # Add Quality Control option
    def launch_quality_control():
        from quality_control_tools.main_quality import main as qc_main
        try:
            qc_main()
        except Exception as e:
            manager.console.print(f"[bold red]Error in Quality Control: {str(e)}[/bold red]")
    
    main_menu.add_option(
        "Quality Control Tools", 
        launch_quality_control,
        "Run data quality control checks"
    )
    
    # Add Analytics menu stub for future expansion
    analytics_menu = main_menu.add_submenu("Data Analytics")
    analytics_menu.add_option(
        "Feature coming soon", 
        lambda: manager.console.print("[yellow]This feature is under development[/yellow]"),
        "Analytics features are coming soon"
    )
    analytics_menu.add_back_option()
    
    # Add Report Generation menu stub for future expansion
    reports_menu = main_menu.add_submenu("Report Generation")
    reports_menu.add_option(
        "Feature coming soon", 
        lambda: manager.console.print("[yellow]This feature is under development[/yellow]"),
        "Report generation features are coming soon"
    )
    reports_menu.add_back_option()
    
    # Add exit option to main menu
    main_menu.add_exit_option("Exit Application", "Exit the InfoBurn application")
    
    return manager


def main() -> None:
    """
    Main entry point for the menu system.
    """
    manager = setup_menus()
    manager.run()


if __name__ == "__main__":
    main()