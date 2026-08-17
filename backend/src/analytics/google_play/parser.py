import csv
import io
import hashlib

class CSVParserError(Exception):
    pass

def detect_encoding_and_decode(content: bytes) -> tuple[str, str]:
    """Detect encoding per Google Play specifications."""
    if content.startswith(b'\xff\xfe') or content.startswith(b'\xfe\xff'):
        return content.decode('utf-16'), 'utf-16-le'
    elif content.startswith(b'\xef\xbb\xbf'):
        return content.decode('utf-8-sig'), 'utf-8-sig'
    
    try:
        return content.decode('utf-8'), 'utf-8'
    except UnicodeDecodeError:
        try:
            return content.decode('utf-16le'), 'utf-16-le'
        except UnicodeDecodeError:
            raise CSVParserError("REPORT_ENCODING_UNSUPPORTED")

def normalize_header(header: str) -> str:
    """Normalize headers: trim, collapse spaces, lowercase."""
    import re
    cleaned = header.strip()
    # Strip BOM if somehow missed
    if cleaned.startswith('\ufeff'):
        cleaned = cleaned[1:]
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.lower()

def compute_schema_fingerprint(headers: list[str]) -> str:
    normalized = [normalize_header(h) for h in headers]
    joined = ",".join(normalized)
    return hashlib.sha256(joined.encode('utf-8')).hexdigest()

def parse_play_report(content_bytes: bytes):
    text, encoding = detect_encoding_and_decode(content_bytes)
    
    f = io.StringIO(text)
    reader = csv.reader(f)
    
    try:
        headers = next(reader)
    except StopIteration:
        return [], [], encoding, "empty"
        
    normalized_headers = [normalize_header(h) for h in headers]
    fingerprint = compute_schema_fingerprint(headers)
    
    rows = []
    for row in reader:
        if not row or not any(row):
            continue
        # Map raw row to dictionary based on normalized headers
        row_dict = dict(zip(normalized_headers, row))
        rows.append(row_dict)
        
    return headers, normalized_headers, rows, encoding, fingerprint
