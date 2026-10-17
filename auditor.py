"""Schedule CSV quality auditor; does not calculate CPM or infer contractual delay."""
import argparse
import csv
import json
from collections import Counter
from datetime import date
from pathlib import Path

REQUIRED = ('activity_id','activity_name','start','finish','duration_days','total_float_days','predecessors','successors')


def parse_date(value):
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def audit(rows, high_float=30, open_end_exempt=None):
    """Return list of deterministic findings from a flat schedule export.

    predecessor/successor columns contain semicolon-separated activity IDs.
    This checks link references, not actual CPM logic or schedule feasibility.
    """
    open_end_exempt = set(open_end_exempt or ())
    findings = []
    def flag(severity, code, aid, detail):
        findings.append({'severity':severity,'code':code,'activity_id':aid,'detail':detail})
    ids = [r.get('activity_id','').strip() for r in rows]
    counts = Counter(x for x in ids if x)
    known = set(counts)
    for idx, row in enumerate(rows, 1):
        aid = row.get('activity_id','').strip() or f'ROW-{idx}'
        if not row.get('activity_id','').strip():
            flag('error','MISSING_ID',aid,'Activity ID is blank')
        elif counts[aid] > 1:
            flag('error','DUPLICATE_ID',aid,'Activity ID occurs more than once')
        if not row.get('activity_name','').strip():
            flag('warning','MISSING_NAME',aid,'Activity name is blank')
        start = parse_date(row.get('start','').strip())
        finish = parse_date(row.get('finish','').strip())
        if not start or not finish:
            flag('error','INVALID_DATE',aid,'Start and finish must use YYYY-MM-DD')
        elif finish < start:
            flag('error','REVERSED_DATES',aid,'Finish is earlier than start')
        try:
            duration = float(row.get('duration_days','').strip())
            if duration < 0:
                flag('error','NEGATIVE_DURATION',aid,'Duration is negative')
        except ValueError:
            flag('error','INVALID_DURATION',aid,'Duration is not numeric')
        try:
            flt = float(row.get('total_float_days','').strip())
            if flt < 0:
                flag('warning','NEGATIVE_FLOAT',aid,f'Total float is {flt:g} days; investigate')
            if flt > high_float:
                flag('warning','HIGH_FLOAT',aid,f'Total float {flt:g} days exceeds threshold {high_float:g}')
        except ValueError:
            flag('error','INVALID_FLOAT',aid,'Total float is not numeric')
        for field, label in [('predecessors','PREDECESSOR'),('successors','SUCCESSOR')]:
            links = [x.strip() for x in row.get(field,'').split(';') if x.strip()]
            if not links and aid not in open_end_exempt:
                flag('warning','MISSING_'+label,aid,f'No {field} listed (may be valid for boundary milestones)')
            for linked in links:
                if linked == row.get('activity_id','').strip():
                    flag('error','SELF_LINK',aid,f'{field}: self-reference')
                elif linked not in known:
                    flag('error','UNKNOWN_LINK',aid,f'{field}: {linked} not found in file')
    return sorted(findings, key=lambda f:({'error':0,'warning':1}[f['severity']], f['activity_id'],f['code']))


def load_csv(path):
    with open(path, newline='', encoding='utf-8-sig') as handle:
        reader = csv.DictReader(handle)
        missing = [name for name in REQUIRED if name not in (reader.fieldnames or [])]
        if missing:
            raise ValueError('Missing required CSV columns: '+', '.join(missing))
        return list(reader)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Audit fictional or exported schedule CSV for quality flags; not a CPM engine.')
    parser.add_argument('csv_file', type=Path)
    parser.add_argument('--high-float', type=float, default=30, help='High total float threshold in days (default: 30)')
    parser.add_argument('--json', dest='json_file', type=Path, help='Write machine-readable findings')
    parser.add_argument('--report', type=Path, help='Write Markdown report')
    parser.add_argument('--exempt-open-end', action='append', default=[], metavar='ACTIVITY_ID')
    args = parser.parse_args(argv)
    try:
        rows = load_csv(args.csv_file)
        findings = audit(rows, args.high_float, args.exempt_open_end)
    except (OSError, ValueError) as exc:
        parser.exit(2, f'Input error: {exc}\n')
    print(f'Audited {len(rows)} activities | {sum(x["severity"]=="error" for x in findings)} errors | {sum(x["severity"]=="warning" for x in findings)} warnings')
    for f in findings:
        print(f'[{f["severity"].upper():7}] {f["activity_id"]:12} {f["code"]:20} {f["detail"]}')
    if args.json_file:
        args.json_file.write_text(json.dumps({'activities':len(rows),'findings':findings},indent=2)+'\n',encoding='utf-8')
    if args.report:
        lines = ['# Schedule Quality Audit','',f'- Input: `{args.csv_file.name}`',f'- Activities: {len(rows)}',f'- Findings: {len(findings)}','', '> Heuristic quality checks only. No CPM network calculation, P6 integration, or delay determination.','', '| Severity | Activity | Check | Detail |','|---|---|---|---|']
        for f in findings:
            safe=lambda s: str(s).replace('|','\\|').replace('\n',' ')
            lines.append('| '+' | '.join(map(safe,[f['severity'],f['activity_id'],f['code'],f['detail']]))+' |')
        args.report.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return 1 if any(f['severity']=='error' for f in findings) else 0


if __name__ == '__main__':
    raise SystemExit(main())
