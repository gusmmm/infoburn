"""
InfoBurn - Burns Critical Care Unit Information System

Main entry point for the InfoBurn application.
"""
from core_tools.menu import setup_menus

def main():
    """
    Main application entry point.
    
    Initializes and runs the main application menu.
    """
    # Set up and run the menu system
    menu_manager = setup_menus()
    menu_manager.run()

if __name__ == "__main__":
    main()
