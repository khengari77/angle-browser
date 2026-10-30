import importlib.util
import struct
import tempfile
import unittest
from pathlib import Path
spec = importlib.util.spec_from_file_location('macho', 'scripts/inspect_macho.py')
macho = importlib.util.module_from_spec(spec)
spec.loader.exec_module(macho)
class MachOTests(unittest.TestCase):
    def run_bytes(self, data):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'test'
            path.write_bytes(data)
            before = path.read_bytes()
            try:
                return macho.inspect(path)
            finally:
                self.assertEqual(before, path.read_bytes())
    def test_minimal(self):
        report = self.run_bytes(struct.pack('<8I', 0xfeedfacf, 0x1000007, 3, 2, 0, 0, 0, 0))
        self.assertEqual(report['slices'][0]['architecture'], 'x86_64')
    def test_universal(self):
        thin = struct.pack('<8I', 0xfeedfacf, 0x100000c, 0, 2, 0, 0, 0, 0)
        fat = struct.pack('>II', 0xcafebabe, 1) + struct.pack('>IIIII', 0x100000c, 0, 28, len(thin), 0) + thin
        self.assertEqual(self.run_bytes(fat)['slices'][0]['architecture'], 'arm64')
    def test_bad_slice(self):
        data = struct.pack('>II', 0xcafebabe, 1) + struct.pack('>IIIII', 0x1000007, 3, 4096, 64, 0)
        with self.assertRaises(ValueError): self.run_bytes(data)
    def test_truncated(self):
        with self.assertRaises(ValueError): self.run_bytes(b'bad')
    def test_bad_command(self):
        data = struct.pack('<8I', 0xfeedfacf, 0x1000007, 3, 2, 1, 8, 0, 0) + struct.pack('<II', 12, 0)
        with self.assertRaises(ValueError): self.run_bytes(data)
if __name__ == '__main__': unittest.main()
