"""Offline regressions; no RPC, subprocess, credentials or writes."""
import json
from pathlib import Path
import random
import unittest
import abi_workbench as abi


class WorkbenchTests(unittest.TestCase):
    def test_keccak_independent_vectors(self):
        # Independently obtained with `cast keccak 0x<61 repeated n times>`.
        vectors = {
            0: 'c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470',
            1: '3ac225168df54212a25c1c01fd35bebfea408fdac2e31ddd6f80a4bbf9a5f1cb',
            134: 'e5de5653994e2fa6729d329b65b5f332dee942a7ea54515e173824c232a4ff91',
            135: '34367dc248bbd832f4e3e69dfaac2f92638bd0bbd18f2912ba4ef454919cf446',
            136: 'a6c4d403279fe3e0af03729caada8374b5ca54d8065329a3ebcaeb4b60aa386e',
            137: 'd869f639c7046b4929fc92a4d988a8b22c55fbadb802c0c66ebcd484f1915f39',
            271: '132f47effd6c8b1b299efa53fe68aece77ec8ae4eb2e294f668eec94f76001e1',
            272: 'cf7fcd4f705ee749930d19ca84561a9bf62516bd90a471545fa2f49fdc7e63c8',
        }
        for n, digest in vectors.items():
            with self.subTest(n=n):
                self.assertEqual(abi.keccak256(b'a' * n).hex(), digest)

    def test_known_selectors(self):
        for signature, expected in {
            'transfer(address,uint256)': 'a9059cbb',
            'balanceOf(address)': '70a08231', 'totalSupply()': '18160ddd',
            'symbol()': '95d89b41', 'decimals()': '313ce567',
        }.items():
            self.assertEqual(abi.keccak256(signature.encode())[:4].hex(), expected)

    def test_alias_signature_from_real_abi_file(self):
        fn, signature = abi.load_function(str(Path(__file__).with_name('alias-example.json')), 'transfer')
        self.assertEqual(signature, 'transfer(address,uint256)')
        self.assertEqual(abi.canonical({'type': 'int'}), 'int256')
        self.assertEqual(fn['inputs'][1]['type'], 'uint')

    def test_exact_integer_input(self):
        for value in [1.9, 1.0, True, False, None, [], {}, '1.0', ' 1', '+1', '0x01', '1e2']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                abi.encode_value('uint256', value)
        self.assertEqual(abi.encode_value('uint256', '123'), abi.word(123))
        self.assertEqual(abi.encode_value('int8', '-128'), abi.word(2**256 - 128))

    def test_integer_widths_and_sign_extension(self):
        rng = random.Random(737)
        for bits in range(8, 257, 8):
            for signed in (False, True):
                t = ('int' if signed else 'uint') + str(bits)
                lo, hi = (-(2**(bits-1)), 2**(bits-1)-1) if signed else (0, 2**bits-1)
                for value in [lo, hi, 0, rng.randint(lo, hi)]:
                    encoded = abi.encode_value(t, value)
                    self.assertEqual(abi.decode_tuple([{'type': t}], encoded)[0]['value'], value)
                for value in [lo-1, hi+1]:
                    with self.assertRaises(ValueError):
                        abi.encode_value(t, value)
                    if bits < 256:
                        with self.assertRaises(ValueError):
                            abi.decode_tuple([{'type': t}], abi.word(value % 2**256))

    def test_gathering_signed_reproduction(self):
        with self.assertRaises(ValueError):
            abi.decode_tuple([{'type': 'int8'}], abi.word(128))
        with self.assertRaises(ValueError):
            abi.decode_tuple([{'type': 'int8'}], abi.word(255))
        self.assertEqual(abi.decode_tuple([{'type': 'int8'}], abi.word(2**256-1))[0]['value'], -1)

    def test_fixed_width_padding(self):
        with self.assertRaises(ValueError):
            abi.decode_tuple([{'type': 'address'}], b'\x01' + b'\0'*31)
        with self.assertRaises(ValueError):
            abi.decode_tuple([{'type': 'bytes1'}], b'\x01'*32)
        for n in range(1, 33):
            t = 'bytes' + str(n)
            v = '0x' + 'ab'*n
            self.assertEqual(abi.decode_tuple([{'type': t}], abi.encode_value(t, v))[0]['value'], v)

    def test_dynamic_abi_layout(self):
        params = [{'type': 'uint'}, {'type': 'string'}, {'type': 'bytes'}]
        values = [9, 'frog 🐸', '0xabcd']
        encoded = abi.encode_tuple(params, values)
        self.assertEqual(encoded[:96], abi.word(9)+abi.word(96)+abi.word(160))
        self.assertEqual([v['value'] for v in abi.decode_tuple(params, encoded)], values)
        for n in [0, 1, 31, 32, 33, 135, 136, 137]:
            p = [{'type': 'string'}]
            self.assertEqual(abi.decode_tuple(p, abi.encode_tuple(p, ['a'*n]))[0]['value'], 'a'*n)

    def test_dynamic_invalid_offsets_and_padding(self):
        p = [{'type': 'bytes'}]
        for malformed in [abi.word(0), abi.word(33)+abi.word(0), abi.word(64),
                          abi.word(32)+abi.word(33)+b'a'*32,
                          abi.word(32)+abi.word(1)+b'a'+b'\0'*30+b'\x01']:
            with self.subTest(data=malformed.hex()), self.assertRaises(ValueError):
                abi.decode_tuple(p, malformed)

    def test_reject_unsupported_types(self):
        for t in ['tuple', 'uint256[][]', 'string[]', 'uint256[0]',
                  'uint256[4097]', 'uint7', 'int264', 'bytes33', 'fixed128x18']:
            with self.assertRaises(ValueError):
                abi.encode_value(t, 0)

    def test_argument_count_and_short_returns(self):
        with self.assertRaises(ValueError):
            abi.encode_tuple([{'type': 'uint'}], [])
        for data in [b'', b'\x00', b'\0'*31]:
            with self.assertRaises(ValueError):
                abi.decode_tuple([{'type': 'uint'}], data)

    def test_invalid_boolean(self):
        with self.assertRaises(ValueError):
            abi.decode_tuple([{'type': 'bool'}], abi.word(2))
        with self.assertRaises(ValueError):
            abi.encode_value('bool', 1)


if __name__ == '__main__':
    unittest.main()
