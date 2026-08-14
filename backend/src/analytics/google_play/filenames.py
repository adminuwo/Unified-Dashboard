import re
from typing import Optional, Dict

class FilenameParserError(Exception):
    pass

def parse_filename(filename: str) -> Dict[str, str]:
    """
    Extracts package name, year, month, and dimension from object name.
    Example: stats/installs/installs_com.uwo.aisa_202607_overview.csv
    """
    if not filename.endswith('.csv'):
        raise FilenameParserError("Not a CSV file")
        
    basename = filename.split('/')[-1]
    if not basename.startswith('installs_'):
        raise FilenameParserError("Invalid prefix")
        
    # Remove installs_ and .csv
    core = basename[len('installs_'):-4]
    
    # Extract _YYYYMM_
    match = re.search(r'_(\d{6})_', core)
    if not match:
        raise FilenameParserError("Missing report month")
        
    report_month_raw = match.group(1)
    year = report_month_raw[:4]
    month = report_month_raw[4:6]
    report_month = f"{year}-{month}"
    
    parts = core.split(f"_{report_month_raw}_")
    if len(parts) != 2:
        raise FilenameParserError("Invalid filename structure")
        
    package_name = parts[0]
    dimension = parts[1]
    
    return {
        "package_name": package_name,
        "year": year,
        "month": month,
        "report_month": report_month,
        "dimension": dimension
    }
