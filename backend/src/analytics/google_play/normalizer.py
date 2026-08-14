from typing import Dict, Any, Optional

class NormalizationError(Exception):
    pass

def safe_int(value: str) -> int:
    if not value or str(value).strip().lower() in ['na', 'null', 'none']:
        return 0
    try:
        return int(float(str(value).replace(',', '').strip()))
    except (ValueError, TypeError):
        return 0

def normalize_dimension(dimension_type: str, row: Dict[str, str]) -> tuple[Optional[str], str]:
    if dimension_type == "overview":
        return None, "__overall__"
        
    # Example: If dimension_type is 'country', look for 'country' in keys
    dim_key = next((k for k in row.keys() if dimension_type.lower() in k.lower()), None)
    
    if not dim_key:
        return None, "__overall__"
        
    raw_val = row.get(dim_key)
    if raw_val is None or str(raw_val).strip() == "":
        return None, "__overall__"
        
    return str(raw_val).strip(), str(raw_val).strip()

def normalize_row(row: Dict[str, str], package_name: str, metric_date: str, dimension_type: str) -> Dict[str, Any]:
    
    dim_val, dim_norm = normalize_dimension(dimension_type, row)
    
    # Map from Google's column names to our internal metrics
    # We use lowercase normalized keys since parser.py normalizes them
    return {
        "metric_date": metric_date,
        "dimension_type": dimension_type,
        "dimension_value": dim_val,
        "dimension_value_normalized": dim_norm,
        "current_device_installs": safe_int(row.get('current device installs', 0)),
        "installs_on_active_devices": safe_int(row.get('installs on active devices', 0)),
        "daily_device_installs": safe_int(row.get('daily device installs', 0)),
        "daily_device_uninstalls": safe_int(row.get('daily device uninstalls', 0)),
        "daily_device_upgrades": safe_int(row.get('daily device upgrades', 0)),
        "current_user_installs": safe_int(row.get('current user installs', 0)),
        "total_user_installs": safe_int(row.get('total user installs', 0)),
        "daily_user_installs": safe_int(row.get('daily user installs', 0)),
        "daily_user_uninstalls": safe_int(row.get('daily user uninstalls', 0)),
        
        # Derived
        "net_daily_device_installs": safe_int(row.get('daily device installs', 0)) - safe_int(row.get('daily device uninstalls', 0)),
        "net_daily_user_installs": safe_int(row.get('daily user installs', 0)) - safe_int(row.get('daily user uninstalls', 0)),
    }
