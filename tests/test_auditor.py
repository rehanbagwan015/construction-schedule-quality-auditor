import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from auditor import audit, load_csv, parse_date

ROOT = Path(__file__).resolve().parents[1]
class AuditTests(unittest.TestCase):
    def setUp(self):
        self.rows = load_csv(ROOT/'samples/fictional_tower_schedule.csv')
    def test_sample_has_nine_rows(self): self.assertEqual(len(self.rows), 9)
    def test_duplicates(self): self.assertIn('DUPLICATE_ID',[x['code'] for x in audit(self.rows)])
    def test_negative_float(self): self.assertIn('NEGATIVE_FLOAT',[x['code'] for x in audit(self.rows)])
    def test_high_float(self): self.assertIn('HIGH_FLOAT',[x['code'] for x in audit(self.rows)])
    def test_unknown_links(self): self.assertIn('UNKNOWN_LINK',[x['code'] for x in audit(self.rows)])
    def test_reversed_dates(self): self.assertIn('REVERSED_DATES',[x['code'] for x in audit(self.rows)])
    def test_missing_links(self): self.assertIn('MISSING_PREDECESSOR',[x['code'] for x in audit(self.rows)])
    def test_iso_dates(self): self.assertIsNone(parse_date('01/02/2027'))
    def test_open_end_exemption(self):
        found = audit(self.rows,open_end_exempt={'A100'})
        self.assertFalse(any(x['activity_id']=='A100' and x['code']=='MISSING_PREDECESSOR' for x in found))
    def test_clean_row(self):
        row=dict(activity_id='X',activity_name='Task',start='2026-01-01',finish='2026-01-02',duration_days='1',total_float_days='0',predecessors='',successors='')
        self.assertEqual(audit([row],open_end_exempt={'X'}),[])
if __name__ == '__main__': unittest.main()
