"""Offline behavior checks; no inspected project code is executed."""
import contextlib
import io
import json
from pathlib import Path
import random
import tempfile
import unittest

import impact


def report_for(graph, entrypoints=()):
    return {'modules': [{'module': n, 'path': n + '.py',
                         'entrypoint': n in entrypoints, 'dynamic_import_lines': []}
                        for n in sorted(graph)],
            'edges': [{'from': n, 'to': m} for n in sorted(graph) for m in sorted(graph[n])],
            'issues': [], 'cycles': []}


class ImpactTests(unittest.TestCase):
    def test_diamond_shortest_path_and_direction(self):
        report = report_for({'cli': {'b', 'a'}, 'a': {'leaf'}, 'b': {'leaf'},
                             'leaf': {'dependency'}, 'dependency': set(), 'other': set()}, ['cli'])
        result = impact.explain(report, ['leaf', 'leaf'])
        self.assertEqual(result['changed'], ['leaf'])
        self.assertEqual(result['summary'], {'module_count': 6, 'affected_count': 4,
                         'dependent_count': 3, 'affected_entrypoints': ['cli']})
        self.assertEqual(next(a for a in result['affected'] if a['module'] == 'cli')['import_path'],
                         ['cli', 'a', 'leaf'])
        self.assertNotIn('dependency', [a['module'] for a in result['affected']])

    def test_multiple_seeds_cycles_self_loops_and_order(self):
        report = report_for({'a': {'b'}, 'b': {'a', 'b'}, 'c': {'b', 'd'}, 'd': set()})
        first = impact.explain(report, ['d', 'a'])
        self.assertEqual(first, impact.explain(report, ['a', 'd', 'a']))
        paths = {a['module']: a['import_path'] for a in first['affected']}
        self.assertEqual(paths, {'a': ['a'], 'b': ['b', 'a'], 'c': ['c', 'd'], 'd': ['d']})
        for a in first['affected']:
            self.assertEqual(a['distance'], len(a['import_path']) - 1)

    def test_unknown_and_empty_selection(self):
        for changed in ([], ['missing'], ['known', 'missing']):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                impact.explain(report_for({'known': set()}), changed)

    def test_against_independent_forward_reachability(self):
        rng = random.Random(24)
        for _ in range(80):
            names = list('abcdefgh')
            graph = {n: {m for m in names if rng.random() < .2} for n in names}
            seeds = set(rng.sample(names, 2))
            expected = {}
            # Independent forward relaxation from every potential importer.
            for start in names:
                dist = {start: 0}
                for _ in names:
                    for n, depth in list(dist.items()):
                        for m in graph[n]:
                            if depth + 1 < dist.get(m, 100):
                                dist[m] = depth + 1
                lengths = [dist[s] for s in seeds if s in dist]
                if lengths:
                    expected[start] = min(lengths)
            result = impact.explain(report_for(graph), seeds)
            self.assertEqual({a['module']: a['distance'] for a in result['affected']}, expected)
            for a in result['affected']:
                path = a['import_path']
                self.assertIn(path[-1], seeds)
                self.assertTrue(all(v in graph[u] for u, v in zip(path, path[1:])))

    def test_deep_chain_is_iterative(self):
        names = [f'n{i:04}' for i in range(1500)]
        graph = {n: {names[i+1]} if i + 1 < len(names) else set() for i, n in enumerate(names)}
        result = impact.explain(report_for(graph), [names[-1]])
        self.assertEqual(result['affected'][0]['import_path'], names)
        self.assertEqual(result['summary']['affected_count'], 1500)

    def test_real_source_encoding_warnings_and_execution_trap(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            root = Path(directory)
            (root / 'leaf.py').write_bytes(b'\xef\xbb\xbfraise RuntimeError("never execute")\n')
            (root / 'cli.py').write_text('import leaf\nimport importlib\n'
                'importlib.import_module("hidden")\nif __name__ == "__main__": pass\n')
            (root / 'broken.py').write_text('def broken(\n')
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = impact.main([str(root), 'leaf', '--json', '--strict'])
            self.assertEqual(status, 1)
            result = json.loads(output.getvalue())
            self.assertEqual(result['summary']['affected_entrypoints'], ['cli'])
            self.assertEqual(result['issues'][0]['type'], 'parse_error')
            self.assertEqual(result['dynamic_imports'], [{'module': 'cli', 'path': 'cli.py', 'line': 3}])
            self.assertIn('1 issues', impact.format_text(result))

    def test_cli_errors_have_no_partial_success_output(self):
        example = Path(__file__).resolve().parents[1] / 'import-map' / 'examples'
        for args in ([str(example), 'not_a_module'], [str(example / 'absent'), 'main'], ['/', 'main']):
            out, err = io.StringIO(), io.StringIO()
            with self.subTest(args=args), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                self.assertEqual(impact.main(args), 2)
            self.assertEqual(out.getvalue(), '')
            self.assertTrue(err.getvalue().startswith('import-impact: '))
            self.assertNotIn('Traceback', err.getvalue())

    def test_original_example_preserves_issues_and_cycles(self):
        example = Path(__file__).resolve().parents[1] / 'import-map' / 'examples'
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            status = impact.main([str(example), 'pkg.helper', '--json'])
        result = json.loads(out.getvalue())
        self.assertEqual(status, 0)
        self.assertEqual([a['module'] for a in result['affected']], ['main', 'pkg.engine', 'pkg.helper'])
        self.assertEqual(result['cycles'], [['pkg.engine', 'pkg.helper']])
        self.assertEqual(len(result['issues']), 1)
        self.assertEqual(result['summary']['affected_entrypoints'], ['main'])


if __name__ == '__main__':
    unittest.main()
