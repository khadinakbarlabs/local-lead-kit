"""Local, reviewed CSV preparation for outreach tools and CRMs."""
import csv
import io
import json
from pathlib import Path
import re

from .core import safe_csv

FIELDS = {
    'email': ['email', 'email_address', 'Email'],
    'first_name': ['first_name', 'firstName', 'First Name'],
    'last_name': ['last_name', 'lastName', 'Last Name'],
    'company_name': ['company_name', 'business_name', 'company', 'Company Name'],
    'website': ['website', 'source_website', 'company_url', 'Website'],
    'phone': ['phone', 'phone_number', 'Phone Number'],
    'source_url': ['source_url', 'maps_source', 'source_website', 'url'],
    'verification_status': ['verification_status', 'validation_status'],
    'observed_at': ['observed_at', 'scrapedAt', 'timestamp'],
}
HEADERS = {
    'instantly': list(FIELDS),
    'smartlead': list(FIELDS),
    'hubspot': ['Email', 'First Name', 'Last Name', 'Company Name', 'Website', 'Phone Number', 'Source URL', 'Verification Status', 'Observed At'],
    'generic': list(FIELDS),
}


def read_rows(path):
    path = Path(path)
    if path.stat().st_size > 16 * 1024 * 1024:
        raise ValueError('Choose an export smaller than 16 MB or split it first.')
    text = path.read_text(encoding='utf-8-sig')
    if path.suffix.lower() == '.csv':
        rows = list(csv.DictReader(io.StringIO(text)))
    elif path.suffix.lower() == '.json':
        value = json.loads(text)
        rows = value.get('items') if isinstance(value, dict) else value
    else:
        raise ValueError('Choose a UTF-8 CSV or JSON export.')
    if not isinstance(rows, list) or len(rows) > 20000 or any(not isinstance(row, dict) for row in rows):
        raise ValueError('Use up to 20,000 record objects or split the file first.')
    if any(any(not isinstance(key, str) for key in row) or any(isinstance(value, (dict, list)) for value in row.values()) for row in rows):
        raise ValueError('Use flat rows with named columns. Flatten nested fields with your assistant first.')
    return rows


def inspect(path):
    rows = read_rows(path)
    return {'rows': len(rows), 'fields': sorted({key for row in rows for key in row}),
            'guidance': 'Review the actual authorized data with your assistant. Preserve sources and distinguish missing data from negative findings.'}


def normalized_email(value):
    value = str(value or '').strip()
    if len(value) > 254 or not re.fullmatch(r'[^\s@,;<>]+@[^\s@,;<>]+\.[^\s@,;<>]+', value):
        return None
    return value.casefold()


def prepare(rows, destination, mapping=None, excluded=()):
    if destination not in HEADERS:
        raise ValueError('Choose instantly, smartlead, hubspot or generic.')
    mapping = {} if mapping is None else mapping
    if not isinstance(mapping, dict) or set(mapping) - set(FIELDS) or any(not isinstance(value, str) for value in mapping.values()):
        raise ValueError('Map supported canonical fields to source column names.')
    available = {key for row in rows for key in row}
    if set(mapping.values()) - available:
        raise ValueError('A mapped source column is absent. Inspect the file first.')
    suppressed = {email for item in excluded if (email := normalized_email(item))}
    accepted = []
    counts = dict(input_rows=len(rows), exported=0, missing_or_invalid_email=0, duplicates=0, excluded=0)
    seen = set()
    for row in rows:
        values = {}
        for field, aliases in FIELDS.items():
            candidates = [mapping[field]] if field in mapping else aliases
            values[field] = next((str(row[name]) for name in candidates if name in row and row[name] is not None and str(row[name]).strip()), '')
        email = normalized_email(values['email'])
        if not email:
            counts['missing_or_invalid_email'] += 1
            continue
        if email in suppressed:
            counts['excluded'] += 1
            continue
        if email in seen:
            counts['duplicates'] += 1
            continue
        seen.add(email)
        values['email'] = email
        accepted.append([safe_csv(values[field]) for field in FIELDS])
    counts['exported'] = len(accepted)
    stream = io.StringIO(newline='')
    writer = csv.writer(stream)
    writer.writerow(HEADERS[destination])
    writer.writerows(accepted)
    return stream.getvalue(), {
        **counts, 'destination': destination, 'columns': HEADERS[destination],
        'mapping': mapping,
        'next_step': 'Review the CSV and map columns in the destination import screen. Source URL, verification status and observation date may need custom fields. An address format check does not establish mailbox delivery or permission to contact.',
    }


def export(input_file, output_file, destination, mapping=None, exclude_file=None):
    rows = read_rows(input_file)
    excluded = []
    if exclude_file:
        for row in read_rows(exclude_file):
            excluded.extend(row.get(name) for name in FIELDS['email'] if row.get(name))
    content, receipt = prepare(rows, destination, mapping, excluded)
    output = Path(output_file)
    if output.resolve() == Path(input_file).resolve():
        raise ValueError('Choose an output file separate from the source export.')
    with output.open('x', encoding='utf-8', newline='') as stream:
        stream.write(content)
    return {**receipt, 'file': str(output)}
