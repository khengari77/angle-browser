import struct
import sys
import unittest
sys.path.insert(0,'scripts')
from x86_literal_refs import lea_candidates, function_starts

class LiteralRefTests(unittest.TestCase):
    def test_rip_relative_lea(self):
        data=b'\x90\x48\x8d\x35'+struct.pack('<i',0x2000-(0x1001+7))+b'\x90'
        rows=lea_candidates(data,{'offset':0,'size':len(data),'address':0x1000},{0x2000})
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['instruction_address'],'0x1001')
        self.assertEqual(rows[0]['target'],'0x2000')
    def test_non_rip_operand_is_not_reference(self):
        data=b'\x48\x8d\x36'+b'\0'*4
        self.assertEqual(lea_candidates(data,{'offset':0,'size':7,'address':0},{7}),[])
    def test_truncated_code_rejected(self):
        with self.assertRaises(ValueError): lea_candidates(b'\x48',{'offset':0,'size':7,'address':0},set())
    def test_function_start_deltas(self):
        data=struct.pack('<4I',0x26,16,16,4)+bytes([0x10,0x81,0x01,0])
        self.assertEqual(function_starts(data,{'file_offset':0},0x1000),[0x1010,0x1091])
    def test_unterminated_delta_rejected(self):
        data=struct.pack('<4I',0x26,16,16,1)+b'\x80'
        with self.assertRaises(ValueError): function_starts(data,{'file_offset':0},0)
if __name__=='__main__': unittest.main()
