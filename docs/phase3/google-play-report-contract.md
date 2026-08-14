# Google Play Install Report Contract

Connector ID: `gplay_main`
Play bucket name: `pubsite_prod_5002243960657921085`
Service-account email: (Using ADC / system default credential)
App code: `aisa`, `ailegal`
Package name: `com.uwo.aisa`, `com.uwo.ailegal`

## Object-name examples
- `stats/installs/installs_com.uwo.aisa_202607_country.csv`
- `stats/installs/installs_com.uwo.aisa_202607_overview.csv`

## Encoding
`UTF-16-LE` (with BOM)

## Delimiter
`,` (Comma)

## Header names
- `Date`
- `Package Name`
- `Country` (or other dimension like `App Version Code`)
- `Daily Device Installs`
- `Daily Device Uninstalls`
- `Daily Device Upgrades`
- `Daily User Installs`
- `Daily User Uninstalls`
- `Current Device Installs`
- `Current User Installs`
- `Installs on Active Devices`
- `Total User Installs`

## Available dimensions
- `country`
- `app_version`
- `carrier`
- `device`
- `os_version`
- `overview` (no dimension)

## Aggregate-row behavior
The overview report file (`_overview.csv`) contains aggregate metrics without a dimension column. This is the canonical source for overall metrics.

## Report date range
Data is aggregated per day and reported in Pacific Time (America/Los_Angeles).

## Source update timestamp
Updated daily via GCS object `updated` metadata.

## Sample row count
~30 rows for monthly overview

## Schema fingerprint
Determined dynamically during parsing by hashing the normalized headers.

## Reconciliation result
TBD during data processing.
