# CSV Merge

Preview a three-way merge of keyed CSV files: one shared baseline and two edited copies. It combines edits to different fields of the same row, accepts identical edits, and treats conflicting edits, concurrent additions, edit-versus-delete cases, and duplicate keys as unresolved. This helps two workers reconcile their exports without silently choosing a winner.

Python 3.9+; standard library only. Keep the sibling `../csv-reconcile/reconcile.py`: this tool reuses its bounded UTF-8 CSV parser and workspace path checks. It reads only the three named CSV files, prints a JSON report by default, and does not modify inputs or send data anywhere. Header order may differ, but the three files must have exactly the same column names. Values remain exact strings.

## One command to see it working

```sh
python3 -B line-2/tools/csv-merge/merge.py line-2/tools/csv-merge/demo-base.csv line-2/tools/csv-merge/demo-left.csv line-2/tools/csv-merge/demo-right.csv --key item --key place --format csv
```

This synthetic trial produced a complete three-row CSV: the `lamp` has the left edit to `count` and the right edit to `note`; both sides made the same `rope` note edit; `flint` is unchanged. Exit status was 0. Omit `--format csv` for a JSON report with decisions and conflicts. Repeat `--key` for composite keys.

Exit statuses: **0** complete merge, **1** unresolved conflicts in JSON mode, **2** invalid input or a CSV export blocked by conflicts. CSV mode writes **no stdout** when conflicts exist. In JSON mode `merged_rows` is only the safe subset when `ready` is false; it is never an approved partial export. All conflicts must be resolved against the source files before exporting CSV. The JSON conflict entries retain full duplicate groups and untrusted raw values; review before sharing.

If redirecting CSV output to a file, choose a new path: a shell opens the destination before this program validates its inputs, so redirecting over an input file would truncate that input. Spreadsheet applications may interpret cell values beginning with formula characters; this tool preserves the original strings without spreadsheet-specific escaping.

The output row order is stable key order; column order comes from the baseline. A missing row is treated as deletion. Adding the same key with differing content is a conflict. Same-field concurrent edits conflict even if other fields can be combined. Differing schemas are rejected, rather than guessed. Exact string comparison means `01` and `1` differ. The inherited input bounds are 16 MiB and 100,000 data records per file. The program holds all three tables and its report in memory. This is an offline data tool: no coin, pool, payment or live chain state is involved.

## Checks performed

```sh
python3 -B -m unittest discover -s line-2/tools/csv-merge -v
```

Seven behavioral tests cover independent edits and reordered columns, same-field conflicts and blocked CSV, delete-versus-edit, safe deletion, concurrent additions, duplicate groups, schema mismatch, exact strings, and stable row ordering. Temporary test inputs live under `test/scratch/`.
