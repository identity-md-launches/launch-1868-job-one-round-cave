"""End-to-end checks for the merge-to-impact handoff."""

from pathlib import Path
import tempfile
import unittest

import drift
import handoff


class HandoffTests(unittest.TestCase):
    def setUp(self):
        scratch = Path('test/scratch').resolve()
        scratch.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.source = self.base / 'source'
        self.source.mkdir()
        (self.source / 'helper.py').write_text('', encoding='utf-8')
        (self.source / 'main.py').write_text(
            'import helper\nif __name__ == "__main__": pass\n', encoding='utf-8')

    def save(self, name):
        path = self.base / name
        text, _ = drift.snapshot(self.source)
        path.write_text(text, encoding='utf-8')
        return path

    def test_independent_edits_reach_the_entry_point(self):
        baseline = self.save('baseline.csv')
        (self.source / 'helper.py').write_text('import json\n', encoding='utf-8')
        left = self.save('left.csv')
        (self.source / 'helper.py').write_text('', encoding='utf-8')
        (self.source / 'side.py').write_text('import csv\n', encoding='utf-8')
        right = self.save('right.csv')
        (self.source / 'helper.py').write_text('import json\n', encoding='utf-8')

        report = handoff.handoff(baseline, left, right, self.source)
        self.assertTrue(report['ready'])
        self.assertEqual(report['changed_modules'], ['helper', 'side'])
        self.assertEqual(report['removed_modules'], [])
        paths = {item['module']: item['import_path'] for item in report['impact']['affected']}
        self.assertEqual(paths['main'], ['main', 'helper'])
        self.assertEqual(report['impact']['summary']['affected_entrypoints'], ['main'])

    def test_conflict_blocks_impact(self):
        baseline = self.save('baseline.csv')
        (self.source / 'helper.py').write_text('import json\n', encoding='utf-8')
        left = self.save('left.csv')
        (self.source / 'helper.py').write_text('import csv\n', encoding='utf-8')
        right = self.save('right.csv')
        report = handoff.handoff(baseline, left, right, self.source)
        self.assertFalse(report['ready'])
        self.assertEqual(report['conflicts'][0]['reason'], 'same_field_edit')
        self.assertNotIn('impact', report)

    def test_mismatched_current_tree_is_rejected(self):
        baseline = self.save('baseline.csv')
        (self.source / 'helper.py').write_text('import json\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'does not match merged snapshot'):
            handoff.handoff(baseline, baseline, baseline, self.source)


if __name__ == '__main__':
    unittest.main()
