"""Checks normalization and the chain hash against the server's test vectors.

The vectors are copied from tellhall-platform (crates/tellhall-core/tests/vectors);
the server is tested against the same files.
"""

import copy
import json
import pathlib
import unittest

from tellhall import ChainError, hall_id, normalize, post_hash, verify_chain

VECTORS = pathlib.Path(__file__).parent / 'vectors'


def load(name):
    return json.loads((VECTORS / name).read_text(encoding='utf-8'))


class NormalizeTest(unittest.TestCase):
    def test_vectors(self):
        for case in load('normalize.json'):
            with self.subTest(raw=case['raw']):
                self.assertEqual(normalize(case['raw']), case['normalized'])
                if case['hall_id'] is None:
                    with self.assertRaises(ValueError):
                        hall_id(case['raw'])
                else:
                    self.assertEqual(hall_id(case['raw']), case['hall_id'])


class ChainTest(unittest.TestCase):
    def setUp(self):
        posts = load('chain.json')
        self.hall = {
            'id': posts[0]['hall_id'],
            'posts': [
                {
                    'seq': p['seq'],
                    'ring_id': p['ring_id'],
                    'published_at': p['published_at'],
                    'body': p['body_public'],
                    'hash': p['hash'],
                }
                for p in posts
            ],
        }

    def test_vectors(self):
        for p in load('chain.json'):
            digest = post_hash(
                bytes.fromhex(p['prev_hash']),
                p['hall_id'],
                p['seq'],
                p['ring_id'],
                p['published_at'],
                p['body_public'],
            )
            self.assertEqual(digest, p['hash'])

    def test_verify_chain(self):
        verify_chain(self.hall)

    def test_edits_are_detected(self):
        for field, value in [
            ('body', 'Edited.'),
            ('ring_id', 'zzzzzzzz'),
            ('published_at', '2026-09-24T17:21:02.123457Z'),
        ]:
            with self.subTest(field=field):
                hall = copy.deepcopy(self.hall)
                hall['posts'][1][field] = value
                with self.assertRaises(ChainError):
                    verify_chain(hall)

    def test_drops_and_reorders_are_detected(self):
        dropped = copy.deepcopy(self.hall)
        del dropped['posts'][1]
        with self.assertRaises(ChainError):
            verify_chain(dropped)
        swapped = copy.deepcopy(self.hall)
        swapped['posts'][0], swapped['posts'][1] = (
            swapped['posts'][1],
            swapped['posts'][0],
        )
        with self.assertRaises(ChainError):
            verify_chain(swapped)


if __name__ == '__main__':
    unittest.main()
