import csv
import io
import json
from pathlib import Path
import tempfile
import unittest

from looksy.exports import export, inspect, prepare, read_rows


class ExportTests(unittest.TestCase):
    def test_missing_duplicate_suppression_and_safe_cells(self):
        rows = [{'email': 'PERSON@example.test', 'business_name': '=FORMULA()', 'validation_status': 'MX_ONLY'},
                {'email': 'person@example.test'}, {'email': 'bad'}, {'business_name': 'No contact'},
                {'email': 'excluded@example.test'}]
        text, report = prepare(rows, 'instantly', excluded=['EXCLUDED@example.test'])
        data = list(csv.DictReader(io.StringIO(text)))
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['company_name'], "'=FORMULA()")
        self.assertEqual(data[0]['verification_status'], 'MX_ONLY')
        self.assertEqual(report['duplicates'], 1)
        self.assertEqual(report['missing_or_invalid_email'], 2)
        self.assertEqual(report['excluded'], 1)
        self.assertEqual(data[0]['first_name'], '')

    def test_explicit_mapping_and_hubspot_headers(self):
        text, report = prepare([{'Contact': 'a@example.test', 'Business': 'A'}], 'hubspot', {'email': 'Contact', 'company_name': 'Business'})
        self.assertEqual(list(csv.DictReader(io.StringIO(text)))[0]['Company Name'], 'A')
        with self.assertRaises(ValueError):
            prepare([{'email': 'a@example.test'}], 'smartlead', {'email': 'absent'})

    def test_inspect_and_export_do_not_modify_sources(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'source.json'
            output = Path(folder) / 'smartlead.csv'
            original = json.dumps({'items': [{'email': 'a@example.test'}]})
            source.write_text(original)
            self.assertEqual(inspect(source)['rows'], 1)
            self.assertEqual(export(source, output, 'smartlead')['exported'], 1)
            self.assertEqual(source.read_text(), original)
            with self.assertRaises(FileExistsError):
                export(source, output, 'smartlead')
            source.write_text('[{"nested": {}}]')
            with self.assertRaises(ValueError):
                read_rows(source)
