# SPDX-License-Identifier: MPL-2.0
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, 'scripts')
from export_workspace import export, Unsupported


def fixture():
    # Independently constructed; never extracted from an Arc profile.
    root = {'id': 'root', 'parentID': None, 'childrenIds': ['folder'], 'data': {'itemContainer': {}}}
    folder = {'id': 'folder', 'parentID': 'root', 'childrenIds': ['a', 'b'], 'title': '研究', 'data': {'list': {}}}
    def tab(key):
        return {'id': key, 'parentID': 'folder', 'title': None, 'data': {'tab': {'savedURL': 'https://example.test/a', 'savedTitle': 'Example'}}}
    return {'version': 1, 'sidebar': {'containers': [{'global': {}}, {
        'spaces': ['space', {'id': 'space', 'title': 'Work', 'containerIDs': ['pinned', 'root']}],
        'items': ['root', root, 'folder', folder, 'a', tab('a'), 'b', tab('b')]}]}}


class ExportTests(unittest.TestCase):
    def test_order_unicode_duplicates_and_no_mutation(self):
        value = fixture(); before = copy.deepcopy(value)
        result = export(value)
        folder = result['spaces'][0]['pinned'][0]
        self.assertEqual(folder['title'], '研究')
        self.assertEqual(len(folder['children']), 2)
        self.assertEqual(value, before)
        self.assertEqual(export(value), result)

    def test_legacy_enum_container_keys(self):
        value = fixture(); space = value['sidebar']['containers'][1]['spaces'][1]
        space['newContainerIDs'] = [{'pinned': {}}, 'root']; del space['containerIDs']
        self.assertEqual(len(export(value)['spaces']), 1)

    def test_bad_version(self):
        for version in [2, True, '1', None]:
            value = fixture(); value['version'] = version
            with self.assertRaises(Unsupported): export(value)

    def test_odd_pairs(self):
        value = fixture(); value['sidebar']['containers'][1]['items'].pop()
        with self.assertRaises(Unsupported): export(value)

    def test_missing_child(self):
        value = fixture(); value['sidebar']['containers'][1]['items'][1]['childrenIds'] = ['missing']
        with self.assertRaises(Unsupported): export(value)

    def test_cycle(self):
        value = fixture(); value['sidebar']['containers'][1]['items'][1]['parentID'] = 'folder'
        with self.assertRaises(Unsupported): export(value)

    def test_unsupported_variant_and_url(self):
        for data in [{'splitView': {}}, {'tab': {'savedURL': 'javascript:alert(1)'}}]:
            value = fixture(); value['sidebar']['containers'][1]['items'][5]['data'] = data
            with self.assertRaises(Unsupported): export(value)

    def test_cli_input_untouched_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, target = Path(tmp)/'input.json', Path(tmp)/'out.json'
            source.write_text(json.dumps(fixture())); original = source.read_bytes()
            command = [sys.executable, 'scripts/export_workspace.py', str(source), '--output', str(target)]
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 2)
            self.assertEqual(source.read_bytes(), original)
            self.assertEqual(subprocess.run([*command[:-1], str(source)], capture_output=True).returncode, 2)
            self.assertEqual(source.read_bytes(), original)


class DepthTests(unittest.TestCase):
    def chain(self, count, reverse=False):
        records = []
        for i in range(count):
            records.append((str(i), {'id': str(i),
                'parentID': str(i-1) if i else None,
                'childrenIds': [str(i+1)] if i+1<count else [],
                'data': {'list': {}} if i else {'itemContainer': {}}}))
        if reverse:
            records.reverse()
        return {'version': 1, 'sidebar': {'containers': [{
            'spaces': ['space', {'containerIDs': ['pinned', '0']}],
            'items': [v for pair in records for v in pair]}]}}

    def test_depth_boundary(self):
        self.assertEqual(len(export(self.chain(130))['spaces']), 1)
        with self.assertRaisesRegex(Unsupported, 'nesting'):
            export(self.chain(131))

    def test_deep_ancestors_rejected_with_bounded_work(self):
        # Deterministic operation budget, independent of machine speed. Abort
        # early if ancestor validation regresses to walking full deep chains.
        for reverse in (False, True):
            value = self.chain(8000, reverse)
            reads = [0]
            class Counted(dict):
                def get(self, key, default=None):
                    if key == 'parentID':
                        reads[0] += 1
                        if reads[0] > 25000:
                            raise AssertionError('Unbounded ancestor traversal')
                    return super().get(key, default)
            items = value['sidebar']['containers'][0]['items']
            items[1::2] = [Counted(item) for item in items[1::2]]
            with self.assertRaisesRegex(Unsupported, 'nesting'):
                export(value)
