"""
Windows-safe utilities for testing with emojis
"""

import sys
import os
from typing import Any, Optional


def is_windows() -> bool:
    """Check if running on Windows."""
    return sys.platform == "win32"


def safe_print(text: str, file: Optional[Any] = None) -> None:
    """
    Safe print function that handles emojis on Windows.
    
    Args:
        text: Text to print (may contain emojis)
        file: Output file (default: sys.stdout)
    """
    if file is None:
        file = sys.stdout
    
    try:
        print(text, file=file)
    except UnicodeEncodeError:
        # On Windows, try to encode with errors='replace'
        if is_windows():
            try:
                # Try with UTF-8 encoding
                file.buffer.write(text.encode('utf-8'))
                file.buffer.write(b'\n')
                file.buffer.flush()
            except (AttributeError, UnicodeEncodeError):
                # Fallback: replace emojis with text
                safe_text = text.encode('ascii', errors='replace').decode('ascii')
                print(safe_text, file=file)
        else:
            # On other platforms, just print normally
            print(text, file=file)


def safe_log(logger, level: str, message: str) -> None:
    """
    Safe logging function that handles emojis on Windows.
    
    Args:
        logger: Logger instance
        level: Log level ('info', 'error', 'warning', 'debug')
        message: Log message (may contain emojis)
    """
    try:
        getattr(logger, level)(message)
    except UnicodeEncodeError:
        if is_windows():
            # Replace emojis with text for logging
            safe_message = message.encode('ascii', errors='replace').decode('ascii')
            getattr(logger, level)(safe_message)
        else:
            getattr(logger, level)(message)


def get_console_encoding() -> str:
    """Get console encoding for current platform."""
    if is_windows():
        try:
            # Try to get Windows console encoding
            import locale
            return locale.getpreferredencoding()
        except:
            return 'cp1251'  # Default Windows encoding
    else:
        return 'utf-8'


def setup_windows_console() -> None:
    """Setup Windows console for UTF-8 support."""
    if is_windows():
        try:
            # Try to set UTF-8 mode
            os.system('chcp 65001 > nul 2>&1')
        except:
            pass


def create_test_environment() -> dict:
    """Create test environment variables for Windows compatibility."""
    env = os.environ.copy()
    
    if is_windows():
        # Set UTF-8 environment variables
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONLEGACYWINDOWSSTDIO'] = '1'
        
        # Try to set console to UTF-8
        try:
            os.system('chcp 65001 > nul 2>&1')
        except:
            pass
    
    return env
