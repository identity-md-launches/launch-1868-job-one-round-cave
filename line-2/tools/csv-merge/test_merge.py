"""Behavioral checks for safe three-way CSV reconciliation."""
import csv
import io
from pathlib import Path
import tempfile
import unittest

import merge


class MergeTests(unittest.TestCase):
    def setUp(self):
        scratch = Path('test/scratch').resolve()
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def table(self, name, text):
        path = self.folder / name
        path.write_text(text, encoding='utf-8')
        return path

    def compare(self, b, l, r, keys=('id',)):
        return merge.merge(self.table('base.csv', b), self.table('left.csv', l),
                           self.table('right.csv', r), keys)

    def test_independent_fields_and_column_reorder(self):
        result = self.compare('id,a,b\nx,0,0\n', 'id,a,b\nx,1,0\n',
                              'b,id,a\n2,x,0\n')
        self.assertTrue(result['ready'])
        self.assertEqual(result['merged_rows'], [{'id': 'x', 'a': '1', 'b': '2'}])
        self.assertEqual(result['summary']['decisions']['combined'], 1)
        self.assertEqual(list(csv.DictReader(io.StringIO(merge.render_csv(result))))[0]['b'], '2')

    def test_same_field_edit_is_conflict_and_csv_is_blocked(self):
        result = self.compare('id,a\nx,0\n', 'id,a\nx,1\n', 'id,a\nx,2\n')
        self.assertFalse(result['ready'])
        self.assertEqual(result['conflicts'][0]['fields']['a'],
                         {'base': '0', 'left': '1', 'right': '2'})
        with self.assertRaises(merge.InputError):
            merge.render_csv(result)

    def test_delete_against_edit_is_conflict(self):
        result = self.compare('id,a\nx,0\n', 'id,a\n', 'id,a\nx,1\n')
        self.assertEqual(result['conflicts'][0]['reason'], 'delete_vs_edit')

    def test_unedited_other_side_accepts_deletion(self):
        result = self.compare('id,a\nx,0\n', 'id,a\n', 'id,a\nx,0\n')
        self.assertTrue(result['ready'])
        self.assertEqual(result['summary']['decisions']['deleted'], 1)
        self.assertEqual(merge.render_csv(result), 'id,a\n')

    def test_concurrent_add_and_duplicate_group(self):
        result = self.compare('id,a\n', 'id,a\nx,1\ny,2\ny,3\n',
                              'id,a\nx,2\ny,4\n')
        self.assertEqual([c['reason'] for c in result['conflicts']],
                         ['concurrent_add', 'duplicate_key'])
        self.assertEqual(len(result['conflicts'][1]['left']), 2)

    def test_changed_schema_rejected(self):
        with self.assertRaisesRegex(merge.InputError, 'same column names'):
            self.compare('id,a\nx,0\n', 'id,a\nx,0\n', 'id,b\nx,0\n')

    def test_exact_text_and_order_independence(self):
        result = self.compare('id,a\nx,01\ny,2\n', 'id,a\ny,2\nx,01\n',
                              'id,a\ny,2\nx,1\n')
        self.assertEqual(result['merged_rows'], [{'id': 'x', 'a': '1'}, {'id': 'y', 'a': '2'}])
        self.assertEqual(result['summary']['decisions']['right'], 1)


if __name__ == '__main__':
    unittest.main()
