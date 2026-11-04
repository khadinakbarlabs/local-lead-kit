# Existing data and destination formats

Use the active assistant's authorized file tools to analyze a supplied export. The bundled toolbox can inspect flat UTF-8 CSV and JSON arrays, including saved results with an `items` array.

```
python3 <skill-dir>/scripts/toolbox.py inspect-data --input-file <authorized-file>
python3 <skill-dir>/scripts/toolbox.py export --input-file <authorized-file> --destination instantly --output-file <new-file.csv>
```

Destinations are `instantly`, `smartlead`, `hubspot`, and `generic`. The exporter creates a local CSV for review and import through the destination. Use the destination import screen to confirm column mapping. Supported fields are email, first_name, last_name, company_name, website, phone, source_url, verification_status and observed_at. Extra provenance columns may require custom properties. Unknown personal names remain blank.

For different source headers supply `--mapping-file <file.json>`, for example `{"email":"Contact address","company_name":"Business"}`. The source columns must exist. `--exclude-file <file.csv>` accepts known email exclusions. Compare against the user's authorized suppression list when preparing outreach data. The receipt gives exported, duplicate, excluded and missing/invalid-email counts. Address syntax and existing check labels stay distinct from confirmed deliverability.

Input is capped at 16 MB and 20,000 flat records. Ask the assistant to flatten nested data or split larger files deliberately. Existing output files are preserved. Research rows without an email remain available in their source file and regular research export. Preparing a contact import requires a usable email for each included row.

For API connections, use the destination's supported host tools or official API only after the user specifies the destination, permitted records and action. Preview mappings and reconcile write receipts before claiming delivery. An imported lead can enter a campaign in some services, so establish the exact import behavior before writing. Keep credentials in the destination's private connection. Creating exports does not require destination credentials.

Official import references checked 4 November 2026.

- [Instantly import troubleshooting and headers](https://help.instantly.ai/en/articles/13644475-why-are-leads-not-uploading)
- [Smartlead column mapping and custom variables](https://helpcenter.smartlead.ai/en/articles/409-how-to-map-csv-columns-in-smartlead-campaigns)
- [HubSpot contact imports](https://knowledge.hubspot.com/import-and-export/import-contacts-quick-import)
