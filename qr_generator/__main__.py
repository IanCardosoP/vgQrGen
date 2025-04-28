"""
Main entry point for the QR Generator application.

This module initializes the logging system and starts the GUI application.
"""

import sys
import argparse
from .utils.logging_utils import LogManager
from .gui.main_window import MainWindow

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="WiFi QR Code Generator - GUI and CLI tool"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    return parser.parse_args()

def main():
    """Main entry point for the application."""
    args = parse_args()
    
    # Initialize logging
    LogManager(debug=args.debug)
    
    try:
        # Start GUI
        app = MainWindow()
        app.run()
        return 0
    except Exception as e:
        print(f"Error starting application: {str(e)}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())