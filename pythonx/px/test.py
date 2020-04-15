# coding=utf8

import unittest
import types

import px.whitespaces as whitespaces
import px.identifiers as identifiers

from px.identifiers import Identifier


class CommonTestCase(unittest.TestCase):
    def testIdentifierUnderCursor(self):
        self.assertEqual(
            identifiers.get_under_cursor(["abc.def"], (0, 2)),
            Identifier("ab", (0, 0))
        )
        self.assertEqual(
            identifiers.get_under_cursor(["abc.def"], (0, 4)),
            Identifier("abc.", (0, 0))
        )
        self.assertEqual(
            identifiers.get_under_cursor(["abc.def"], (0, 7)),
            Identifier("abc.def", (0, 0))
        )

    def testHigherIndent(self):
        self.assertEqual( whitespaces.get_higher_indent(['a', 'b'], (1, 0)),
            None
        )
        self.assertEqual(
            whitespaces.get_higher_indent(['a', '\tb'], (1, 0)),
            ('a', 0)
        )

    def testHigherIndentMatch(self):
        self.assertEqual(
            whitespaces.match_higher_indent(['a', '\tb', '\t\tc'],
                (1, 0), 'a'),
            ('a', 0)
        )
        self.assertEqual(
            whitespaces.match_higher_indent(['a', '', '\t\tc'], (2, 0), 'a'),
            ('a', 0)
        )

    def testPossibleIdentifier(self):
        result = identifiers.extract_possible_backward(['a b c'], (0, 5))
        self.assertIsInstance(
            result[0], types.GeneratorType
        )
        for item in result:
            self.assertEqual(
                list(item),
                [
                    Identifier('c', (0, 4)),
                    Identifier('b', (0, 2)),
                    Identifier('a', (0, 0))
                ]
            )

    def testGetLastUsedIdentifier(self):
        test_identifiers = [
            Identifier('c', (1, 5)),
            Identifier('b', (1, 3)),
            Identifier('a', (1, 1))
        ]
        self.assertEqual(
            identifiers.get_last_used(test_identifiers),
            Identifier('c', (1, 5))
        )
        self.assertEqual(
            identifiers.get_last_used(test_identifiers,
                Identifier('c', (1, 5))),
            Identifier('b', (1, 3))
        )
        self.assertEqual(
            identifiers.get_last_used(test_identifiers,
                Identifier('c', (1, 5)),
                should_skip=lambda x: x.name == 'b'),
            Identifier('a', (1, 1))
        )

    def testCanEnsureNewlines(self):
        self.assertEqual(
            whitespaces.ensure_newlines(['a'], (0, '_'), 1),
            (['', 'a'], 0, 1)
        )
        self.assertEqual(
            whitespaces.ensure_newlines(['', 'a'], (1, '_'), 1),
            (['', 'a'], 0, 0)
        )
        self.assertEqual(
            whitespaces.ensure_newlines(['', 'a'], (1, '_'), 2),
            (['', '', 'a'], 0, 1)
        )
        self.assertEqual(
            whitespaces.ensure_newlines(['a', 'b', 'c'], (2, '_'), 1),
            (['a', 'b', '', 'c'], 2, 1)
        )
        self.assertEqual(
            whitespaces.ensure_newlines(['a', 'b', 'c'], (1, '_'), 2),
            (['a', '', '', 'b', 'c'], 1, 2)
        )
        self.assertEqual(
            whitespaces.ensure_newlines(['a', '', 'b'], (2, '_'), 1),
            (['a', '', 'b'], 1, 0)
        )

if __name__ == '__main__':
    unittest.main()
