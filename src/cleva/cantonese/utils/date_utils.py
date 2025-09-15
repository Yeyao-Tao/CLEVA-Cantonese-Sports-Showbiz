#!/usr/bin/env python3
"""
Utilities for handling date parsing.
"""

def parse_date(date_str):
    """Parse WikiData date string to extract year."""
    if isinstance(date_str, str) and len(date_str) >= 4:
        return int(date_str[:4])
    return None
