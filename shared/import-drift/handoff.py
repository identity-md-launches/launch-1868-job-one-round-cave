#!/usr/bin/env python3
"""Merge import snapshots and trace their confirmed changes to Python entry points."""

import argparse
import csv
import io
import json
import sys

import drift
import impact
import merge
import reconcile


def table(path):
    """Read one exact import-drift snapshot, retaining duplicate groups."""
    header, groups, count = reconcile.load_table(drift.workspace_path(path), ('module',))
    if set(header) != set(drift.FIELDS):
        raise ValueError('all inputs must have import-drift/v1 snapshot columns')
    return groups, count


def handoff(base, left, right, current_root):
    """Return a merge plus impact only when current source matches the merged snapshot."""
    inputs = [table(path)[0] for path in (base, left, right)]
    merged = merge.merge(base, left, right, ('module',))
    result = {'schema': 'import-handoff/v1', 'ready': merged['ready'],
              'merge_summary': merged['summary'], 'conflicts': merged['conflicts']}
    if not merged['ready']:
        return result

    # A path through the wrong checkout would be a misleading impact claim.
    merged_rows = {row['module']: row for row in merged['merged_rows']}
    current_csv, scan = drift.snapshot(current_root)
    current_rows = {row['module']: row for row in csv.DictReader(io.StringIO(current_csv))}
    if current_rows != merged_rows:
        missing = sorted(set(merged_rows) - set(current_rows))
        extra = sorted(set(current_rows) - set(merged_rows))
        differing = sorted(name for name in set(current_rows) & set(merged_rows)
                           if current_rows[name] != merged_rows[name])
        raise ValueError('current source does not match merged snapshot: '
                         + json.dumps({'missing': missing, 'extra': extra,
                                       'differing': differing}, sort_keys=True))

    baseline = {key[0]: group[0]['values'] for key, group in inputs[0].items()}
    changed = sorted(name for name, row in merged_rows.items()
                     if baseline.get(name) != row)
    removed = sorted(set(baseline) - set(merged_rows))
    result['changed_modules'] = changed
    result['removed_modules'] = removed
    result['impact'] = impact.explain(scan, changed) if changed else None
    result['scan_summary'] = scan['summary']
    result['limits'] = ('Static local imports only. Removed modules have no current '
                        'reverse path; review unresolved imports separately.')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('base', help='baseline import-drift CSV inside workspace')
    parser.add_argument('left', help='first edited import-drift CSV inside workspace')
    parser.add_argument('right', help='second edited import-drift CSV inside workspace')
    parser.add_argument('current_root', help='source tree corresponding exactly to the merged snapshot')
    args = parser.parse_args(argv)
    try:
        report = handoff(args.base, args.left, args.right, args.current_root)
    except (OSError, ValueError, KeyError, RecursionError) as exc:
        print(json.dumps({'error': str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if report['ready'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
