# SPDX-License-Identifier: MPL-2.0
"""Synthetic PE declarations; no proprietary fixture bytes."""
import importlib.util
import struct
import unittest

spec = importlib.util.spec_from_file_location('binary_reconstruction', 'scripts/binary_reconstruction.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class PEInventoryTests(unittest.TestCase):
    def fixture(self):
        data = bytearray(512)
        data[:2] = b'MZ'
        struct.pack_into('<I', data, 0x3c, 0x80)
        data[0x80:0x84] = b'PE\0\0'
        struct.pack_into('<HHIIIHH', data, 0x84, 0x8664, 1, 0, 0, 0, 2, 0x22)
        struct.pack_into('<H', data, 0x98, 0x20b)
        struct.pack_into('<8sIIII', data, 0x9a, b'.text\0\0\0', 8, 0x1000, 8, 256)
        return data

    def test_section_coordinates(self):
        data = self.fixture()
        before = bytes(data)
        p = m.inspect_pe(data)
        self.assertEqual(p['machine'], '0x8664')
        self.assertEqual(p['sections'][0]['file_offset'], 256)
        self.assertEqual(bytes(data), before)

    def test_truncated_headers(self):
        with self.assertRaises(ValueError):
            m.inspect_pe(b'MZ')

    def test_section_outside_file(self):
        data = self.fixture()
        struct.pack_into('<I', data, 0x9a+20, 510)
        with self.assertRaises(ValueError):
            m.inspect_pe(data)

    def test_excessive_section_count(self):
        data = self.fixture()
        struct.pack_into('<H', data, 0x86, 97)
        with self.assertRaises(ValueError):
            m.inspect_pe(data)


class FunctionStartOwnershipTests(unittest.TestCase):
    def fixture(self):
        data = bytearray(512)
        data[:4] = bytes.fromhex('cffaedfe')
        struct.pack_into('<II', data, 16, 2, 88)
        struct.pack_into('<II16sQQQQiiII', data, 32, 0x19, 72,
                         b'__TEXT', 0x100000000, 512, 0, 512, 7, 5, 0, 0)
        struct.pack_into('<IIII', data, 104, 0x26, 16, 256, 3)
        data[256:259] = bytes([16, 32, 0])
        return data

    def test_relative_function_start_is_not_caller(self):
        rows = m.function_start_ownership(self.fixture(), [0x100000100, 0x100000101])['sites']
        self.assertEqual(rows[0]['record_target'], '0x100000010')
        self.assertEqual(rows[1]['record_target'], '0x100000030')
        self.assertEqual(rows[0]['record_size'], 1)

    def test_truncated_uleb_rejected(self):
        data = self.fixture()
        data[256:259] = bytes([128, 128, 128])
        with self.assertRaises(ValueError):
            m.function_start_ownership(data, [0x100000100])

    def test_reference_outside_file_mapping_rejected(self):
        with self.assertRaises(ValueError):
            m.function_start_ownership(self.fixture(), [0x200000000])
