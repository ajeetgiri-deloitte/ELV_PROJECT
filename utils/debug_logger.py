# utils/debug_logger.py
import os
import sys
import traceback
from datetime import datetime

def log_debug(message, error=None):
    """
    Simple debug logger that writes to a file in the project root
    """
    # Get the project root directory
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_file = os.path.join(BASE_DIR, 'debug.log')
    
    # Create log entry
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    log_entry = f"[{timestamp}] {message}\n"
    
    if error:
        log_entry += f"Error: {str(error)}\n"
        log_entry += f"Traceback: {traceback.format_exc()}\n"
    
    log_entry += "-" * 80 + "\n"
    
    # Write to file
    try:
        with open(log_file, 'a') as f:
            f.write(log_entry)
        return True
    except Exception as e:
        print(f"Failed to write debug log: {e}")
        return False