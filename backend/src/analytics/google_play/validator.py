from typing import Dict, List
import re

class ValidationError(Exception):
    pass

def validate_row(row: Dict[str, str], expected_package: str, expected_month: str):
    """
    Validates a single row against business rules.
    """
    pkg = row.get('package name')
    if not pkg:
        raise ValidationError("Missing package name in row")
    if pkg != expected_package:
        raise ValidationError(f"Package mismatch: expected {expected_package}, got {pkg}")
        
    date_val = row.get('date')
    if not date_val:
        raise ValidationError("Missing date in row")
        
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_val):
        raise ValidationError(f"Invalid date format: {date_val}")
        
    row_month = date_val[:7]
    if row_month != expected_month:
        raise ValidationError(f"Date {date_val} does not belong to expected month {expected_month}")

def validate_schema(headers: List[str]):
    """
    Ensures required columns exist.
    """
    required = {
        'date',
        'package name',
        'daily device installs',
        'daily device uninstalls',
        'daily device upgrades',
        'daily user installs',
        'daily user uninstalls'
    }
    
    missing = required - set(headers)
    if missing:
        raise ValidationError(f"Missing required columns: {missing}")
