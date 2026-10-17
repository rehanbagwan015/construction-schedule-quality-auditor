# Construction Schedule Quality Auditor

**LinkedIn Lab 30 — Project 03/30 | GitHub + Python**

A small, dependency-free Python command-line tool that flags potential data-quality issues in a construction schedule CSV export. Created as an educational project-controls portfolio demonstration.

> **Important:** This is **not** Primavera P6, a CPM engine, a DCMA 14-point assessment, an automated delay analysis, or an integration with live construction data. It cannot determine whether a project is delayed. Flags require professional interpretation.

## Quick start (Windows PowerShell)

Requires Python 3.9 or newer. Download or clone this repository, then run from its folder:

```powershell
py -3 auditor.py samples/fictional_tower_schedule.csv --report audit-report.md --json audit-results.json
py -3 -m unittest discover -s tests -v
```

The sample intentionally contains **fictional** anomalies. The command returns exit code `1` if it finds any error-level issues (useful in CI); `0` means no errors, though warnings may remain; `2` indicates invalid input.

## Expected input format

A UTF-8 CSV with these exact headers:

| Column | Meaning |
|---|---|
| `activity_id` | Unique activity identifier |
| `activity_name` | Description |
| `start`, `finish` | ISO dates `YYYY-MM-DD` |
| `duration_days` | Numeric duration as exported, **not independently recalculated** |
| `total_float_days` | Numeric total float as exported |
| `predecessors`, `successors` | Semicolon-separated activity IDs; leave blank if none |

**Export adaptation:** Real P6 exports vary by layout, calendar, relationship formatting, and encoding. Map your CSV columns to this format before using the auditor. Link checks work only on activities present in the supplied file; partial extracts may produce false positives. The tool does not infer activity calendars or relationship lags.

## Checks

- Blank and duplicate activity IDs; blank activity names
- Invalid/reversed dates, nonnumeric/negative duration
- Nonnumeric, negative or high total float (`--high-float 30` by default)
- Missing predecessor/successor lists (may be valid for start/end milestones)
- Unknown activity references and self-referencing links

Set exemptions for legitimate boundary activities using `--exempt-open-end A100` (repeat as needed).

## Reporting

Terminal summary plus optional JSON and Markdown reports. `--help` lists flags. Results are reproducible and do not require internet access, paid APIs, or third-party packages.

## Limitations and future work

This MVP **does not** check relationship reciprocity, calculate a CPM network, evaluate constraints, calendars, leads/lags, out-of-sequence progress, baseline variance, or contractual delay. A future version could add a separate parser for a user-provided P6 XER export with carefully documented semantics and tests.

## Portfolio

Built as **LinkedIn Lab 30 · 03/30**, demonstrating Python validation, unit tests, reporting and GitHub workflow practices applied to construction project controls. All bundled schedule data are fictional.
