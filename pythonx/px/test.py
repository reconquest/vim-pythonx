# coding=utf8

import unittest
from util import *

class CommonTestCase(unittest.TestCase):
    def testIdentifierUnderCursor(self):
        self.assertEqual(
            get_identifier_under_cursor(["abc.def"], (0, 2)),
            "ab"
        )
        self.assertEqual(
            get_identifier_under_cursor(["abc.def"], (0, 4)),
            "abc."
        )
        self.assertEqual(
            get_identifier_under_cursor(["abc.def"], (0, 7)),
            "abc.def"
        )

    def testHigherIndent(self):
        self.assertEqual(
            get_higher_ident(['a', 'b'], (2, 0)),
            None
        )
        self.assertEqual(
            get_higher_ident(['a', '\tb'], (2, 0)),
            ('a', 1)
        )

    def testHigherIndentMatch(self):
        self.assertEqual(
            match_higher_indent(['a', '\tb', '\t\tc'], (3, 0), 'a'),
            ('a', 1)
        )
        self.assertEqual(
            match_higher_indent(['a', '', '\t\tc'], (3, 0), 'a'),
            ('a', 1)
        )

    def testPossibleIdentifiers(self):
        self.assertEqual(
            list(get_possible_identifiers(['a b c'], (1, 5))),
            [
                ('c', (1, 5)),
                ('b', (1, 3)),
                ('a', (1, 1))
            ]
        )

    def testGetLastUsedVar(self):
        identifiers = [
            ('c', (1, 5)),
            ('b', (1, 3)),
            ('a', (1, 1))
        ]
        self.assertEqual(
            get_last_used_var(identifiers),
            ('c', (1, 5))
        )
        self.assertEqual(
            get_last_used_var(identifiers, ('c', (1, 5))),
            ('b', (1, 3))
        )
        self.assertEqual(
            get_last_used_var(identifiers, ('c', (1, 5)),
                should_skip=lambda x: x[0]=='b'),
            ('a', (1, 1))
        )

if __name__ == '__main__':
    unittest.main()
