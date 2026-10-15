"""Arrays of static scalars, including an official Solidity ABI example."""
import unittest

import abi_workbench as abi


class ScalarArrayTests(unittest.TestCase):
    def test_solidity_spec_dynamic_array_vector(self):
        # https://docs.soliditylang.org/en/latest/abi-spec.html#use-of-dynamic-types
        # Published f(uint256,uint32[],bytes10,bytes) example, 0x123,
        # [0x456, 0x789], "1234567890", "Hello, world!".
        params = [{'type': t} for t in ('uint256', 'uint32[]', 'bytes10', 'bytes')]
        values = [0x123, [0x456, 0x789], '0x31323334353637383930',
                  '0x48656c6c6f2c20776f726c6421']
        words = [
            '0000000000000000000000000000000000000000000000000000000000000123',
            '0000000000000000000000000000000000000000000000000000000000000080',
            '3132333435363738393000000000000000000000000000000000000000000000',
            '00000000000000000000000000000000000000000000000000000000000000e0',
            '0000000000000000000000000000000000000000000000000000000000000002',
            '0000000000000000000000000000000000000000000000000000000000000456',
            '0000000000000000000000000000000000000000000000000000000000000789',
            '000000000000000000000000000000000000000000000000000000000000000d',
            '48656c6c6f2c20776f726c642100000000000000000000000000000000000000',
        ]
        expected = bytes.fromhex(''.join(words))
        self.assertEqual(abi.keccak256(b'f(uint256,uint32[],bytes10,bytes)')[:4].hex(), '8be65246')
        self.assertEqual(abi.encode_tuple(params, values), expected)
        self.assertEqual([x['value'] for x in abi.decode_tuple(params, expected)], values)

    def test_fixed_array_expands_head_and_aliases_canonicalize(self):
        params = [{'type': 'uint[2]'}, {'type': 'address[]'}, {'type': 'bool'}]
        zto = '0xd782bdea4ef02a0bd391eb9089470c8080f0a68e'
        imd = '0xd34a99bc0f67ae1bbd63c660e6d0b0dd03e263b7'
        values = [[3, 5], [zto, imd], True]
        self.assertEqual(abi.canonical(params[0]), 'uint256[2]')
        encoded = abi.encode_tuple(params, values)
        self.assertEqual(encoded[:128], abi.word(3) + abi.word(5) + abi.word(128) + abi.word(1))
        self.assertEqual(encoded[128:160], abi.word(2))
        self.assertEqual([x['value'] for x in abi.decode_tuple(params, encoded)], values)

    def test_empty_dynamic_array_and_fixed_array_input(self):
        p = [{'type': 'int8[]'}]
        self.assertEqual(abi.encode_tuple(p, [[]]), abi.word(32) + abi.word(0))
        self.assertEqual(abi.decode_tuple(p, abi.word(32) + abi.word(0))[0]['value'], [])
        for value in [1, '[]', {}, [1], [1, 2, 3]]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                abi.encode_value('uint8[2]', value)
        with self.assertRaises(ValueError):
            abi.encode_value('uint8[]', [1, 256])

    def test_reject_malformed_array_return(self):
        p = [{'type': 'bool[]'}]
        for malformed in [
            abi.word(0) + abi.word(0),
            abi.word(32) + abi.word(2) + abi.word(1),
            abi.word(32) + abi.word(1) + abi.word(2),
            abi.word(32) + abi.word(abi.MAX_ARRAY_ITEMS + 1),
        ]:
            with self.subTest(data=malformed.hex()), self.assertRaises(ValueError):
                abi.decode_tuple(p, malformed)
        with self.assertRaises(ValueError):
            abi.decode_tuple([{'type': 'uint8[2]'}], abi.word(1))


if __name__ == '__main__':
    unittest.main()
