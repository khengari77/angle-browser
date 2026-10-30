import importlib.util
import struct
import unittest

spec = importlib.util.spec_from_file_location('swift_fields', 'scripts/swift_fields.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def fixture():
    data=bytearray(0x900)
    struct.pack_into('<8I',data,0,0xfeedfacf,0x1000007,3,2,1,232,0,0)
    struct.pack_into('<II16sQQQQiiII',data,32,0x19,232,b'__TEXT',0x100000000,len(data),0,len(data),7,5,2,0)
    for pos,name,off,size in [(104,b'__swift5_fieldmd',0x200,28),(184,b'__const',0x300,0x600)]:
        struct.pack_into('<16s16sQQIIIIIIII',data,pos,name,b'__TEXT',0x100000000+off,size,off,0,0,0,0,0,0,0)
    struct.pack_into('<iiHHI',data,0x200,0x300-0x200,0,0,12,1)
    struct.pack_into('<Iii',data,0x210,2,0x580-0x214,0x560-0x218)
    data[0x300]=1
    struct.pack_into('<i',data,0x301,0x400-0x301)
    struct.pack_into('<Iii',data,0x400,17,0x450-0x404,0x500-0x408)
    struct.pack_into('<Iii',data,0x450,0,0,0x520-0x458)
    for pos,value in [(0x500,b'Widget\0'),(0x520,b'Unit\0'),(0x560,b'count\0'),(0x580,b'Si\0')]:
        data[pos:pos+len(value)]=value
    return data


class SwiftFieldTests(unittest.TestCase):
    def test_stored_property(self):
        data=bytes(fixture())
        report=m.Image(data).fields('Unit.Widget')
        self.assertEqual(report['descriptor_count'],1)
        self.assertEqual(report['issues'],[])
        row=report['matches'][0]
        self.assertEqual(row['context'],'Unit.Widget')
        self.assertEqual(row['fields'][0]['name'],'count')
        self.assertEqual(row['fields'][0]['mangled_type']['text'],'Si')
        self.assertEqual(data,bytes(fixture()))

    def test_embedded_null_symbolic_pointer(self):
        image=m.Image(bytes(fixture()))
        name=image.string(0x100000300,symbolic=True)
        self.assertEqual(name['bytes_hex'],'01ff000000')
        self.assertEqual(name['symbolic_references'][0]['context'],'Unit.Widget')

    def test_verified_chained_indirect_context(self):
        data=fixture()
        struct.pack_into('<II',data,16,2,248)
        struct.pack_into('<4I',data,264,0x80000034,16,0x600,0x100)
        struct.pack_into('<7I',data,0x600,0,28,0,0,0,1,0)
        struct.pack_into('<II',data,0x61c,1,8)
        struct.pack_into('<IHHQIH',data,0x624,24,4096,6,0,0,1)
        struct.pack_into('<H',data,0x63a,0x700)
        struct.pack_into('<Q',data,0x700,0x400)
        data[0x300]=2
        struct.pack_into('<i',data,0x301,0x700-0x301)
        image=m.Image(bytes(data))
        self.assertEqual(image.string(0x100000300,True)['symbolic_references'][0]['context'],'Unit.Widget')
        # A similar bit-pattern outside the fixup chain is not a pointer.
        with self.assertRaises(ValueError): image.indirect_context(0x100000708)

    def test_unknown_layout_rejected(self):
        data=fixture(); struct.pack_into('<H',data,0x20a,16)
        with self.assertRaises(ValueError): m.Image(data).fields()

    def test_truncated_command_rejected(self):
        with self.assertRaises(ValueError): m.Image(bytes(fixture()[:40]))

    def test_filter_reports_scan_coverage(self):
        report=m.Image(bytes(fixture())).fields('Absent')
        self.assertEqual(report['descriptor_count'],1)
        self.assertEqual(report['matches'],[])

    def test_cyclic_context_preserved_as_unresolved(self):
        data=fixture();struct.pack_into('<i',data,0x404,-4)
        image=m.Image(bytes(data))
        self.assertIn('cyclic',image.string(0x100000300,True)['symbolic_references'][0]['unresolved'])

if __name__=='__main__': unittest.main()
