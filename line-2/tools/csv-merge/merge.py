#!/usr/bin/env python3
"""Offline three-way merge of exact, keyed CSV rows."""
import argparse
import csv
import io
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'csv-reconcile'))
from reconcile import InputError, load_table  # noqa: E402


def merge(base_path, left_path, right_path, keys):
    if not keys or len(set(keys)) != len(keys) or any(not key for key in keys):
        raise InputError('provide distinct, nonempty key columns')
    base_header, base, base_count = load_table(base_path, keys)
    left_header, left, left_count = load_table(left_path, keys)
    right_header, right, right_count = load_table(right_path, keys)
    if set(base_header) != set(left_header) or set(base_header) != set(right_header):
        raise InputError('all three files must have the same column names; reconcile schema changes first')

    rows = []
    conflicts = []
    decisions = {'unchanged': 0, 'left': 0, 'right': 0, 'both': 0, 'combined': 0, 'deleted': 0}
    for key in sorted(base.keys() | left.keys() | right.keys()):
        groups = (base.get(key, []), left.get(key, []), right.get(key, []))
        key_map = dict(zip(keys, key))
        if any(len(group) > 1 for group in groups):
            conflicts.append({'key': key_map, 'reason': 'duplicate_key',
                              'base': groups[0], 'left': groups[1], 'right': groups[2]})
            continue
        b, l, r = (group[0]['values'] if group else None for group in groups)
        if l == r:
            result = l
            decision = 'unchanged' if l == b else 'both'
        elif l == b:
            result, decision = r, 'right'
        elif r == b:
            result, decision = l, 'left'
        elif b is None:
            conflicts.append({'key': key_map, 'reason': 'concurrent_add', 'left': l, 'right': r})
            continue
        elif l is None or r is None:
            conflicts.append({'key': key_map, 'reason': 'delete_vs_edit',
                              'base': b, 'left': l, 'right': r})
            continue
        else:
            fields = {}
            collision = {}
            for column in base_header:
                bv, lv, rv = b[column], l[column], r[column]
                if lv == rv:
                    fields[column] = lv
                elif lv == bv:
                    fields[column] = rv
                elif rv == bv:
                    fields[column] = lv
                else:
                    collision[column] = {'base': bv, 'left': lv, 'right': rv}
            if collision:
                conflicts.append({'key': key_map, 'reason': 'same_field_edit', 'fields': collision})
                continue
            result, decision = fields, 'combined'
        if result is None:
            decisions['deleted'] += 1
        else:
            rows.append({column: result[column] for column in base_header})
            decisions[decision] += 1

    return {'format': 'csv-merge/v1', 'keys': list(keys), 'columns': base_header,
            'ready': not conflicts, 'summary': {'base_records': base_count,
            'left_records': left_count, 'right_records': right_count,
            'merged_records': len(rows), 'conflicts': len(conflicts), 'decisions': decisions},
            'merged_rows': rows, 'conflicts': conflicts}


def render_csv(result):
    """Render only a complete merge; never present partial rows as a CSV."""
    if not result['ready']:
        raise InputError('merge has conflicts; inspect JSON report before exporting CSV')
    out = io.StringIO(newline='')
    writer = csv.DictWriter(out, fieldnames=result['columns'], lineterminator='\n')
    writer.writeheader()
    writer.writerows(result['merged_rows'])
    return out.getvalue()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('base', help='shared baseline CSV inside the current directory')
    parser.add_argument('left', help='first edited CSV inside the current directory')
    parser.add_argument('right', help='second edited CSV inside the current directory')
    parser.add_argument('--key', action='append', required=True, help='stable key column; repeat for composite keys')
    parser.add_argument('--format', choices=('json', 'csv'), default='json')
    args = parser.parse_args(argv)
    try:
        result = merge(args.base, args.left, args.right, args.key)
        if args.format == 'csv':
            output = render_csv(result)
        else:
            output = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + '\n'
    except (InputError, OSError, ValueError) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    sys.stdout.write(output)
    return 0 if result['ready'] else 1


if __name__ == '__main__':
    sys.exit(main())
