# coding=utf8

import unittest
import collections

import px.langs.go.completion as completion
import px.langs.go.completion.unused as unused


ID = collections.namedtuple('ID', ['position'])

is_func_argument = completion.unused.UnusedIdentifierCompleter._is_func_argument

no_skip = lambda *_: False

class FuncArgumentTestCase(unittest.TestCase):
    def testCanIdentifySoleArgument(self):
        buffer = ['func xxx(blah)']

        tests = [
            ((0, 10), True),
            ((0, 9), True),
            ((0, 8), False),
            ((0, 0), False),
            ((0, 13), True),
            ((0, 14), False),
        ]

        self._runTableTests(buffer, tests)

    def testCanIdentifySecondArgument(self):
        buffer = ['func xxx(blah, lol)']

        tests = [
            ((0, 15), True),
            ((0, 16), True),
            ((0, 17), True),
            ((0, 18), True),
            ((0, 19), False),
        ]

        self._runTableTests(buffer, tests)

    def testCanIdentifyArgumenOnNewLine(self):
        buffer = ['func yyy(', 'blah)']

        tests = [
            ((1, 0), True),
            ((1, 1), True),
            ((1, 2), True),
            ((1, 5), False),
        ]

        self._runTableTests(buffer, tests)

    def testCanIdentifySecondArgumenOnNewLine(self):
        buffer = ['func yyy(', 'bla', 'a)']

        tests = [
            ((2, 0), True),
            ((2, 1), True),
            ((2, 2), False),
        ]

        self._runTableTests(buffer, tests)

    def testCanIdentifyArgumentAfterFunc(self):
        buffer = ['func yyy(func()', 'bla)']
        tests = [
            ((1, 0), True),
            ((1, 1), True),
            ((1, 3), True),
            ((1, 4), False),
        ]

        self._runTableTests(buffer, tests)

    def testCanIdentifyArgumentAfterFunc(self):
        buffer = ['func yyy(a func()', 'bla)']

        tests = [
            ((1, 0), True),
            ((1, 1), True),
            ((1, 3), True),
            ((1, 4), False),
        ]

        self._runTableTests(buffer, tests)

    def testCanIdentifyArgumentAfterFunc(self):
        buffer = ['func yyy(a func(),', 'bla)']

        tests = [
            ((1, 0), True),
            ((1, 1), True),
            ((1, 3), True),
            ((1, 4), False),
        ]

        self._runTableTests(buffer, tests)

    def testCanIdentifyArgumentOutsideFunc(self):
        buffer = ['func yyy(a func(),', 'bla)', 'print(doh)']

        tests = [
            ((2, 1), False),
            ((2, 8), False),
        ]

        self._runTableTests(buffer, tests)


    def testCanIdentifyArgumentOutsideFuncAfterCall(self):
        buffer = ['func yyy(a func(),', 'bla)', 'print(doh)', 'wazap']

        tests = [
            ((3, 1), False),
            ((3, 5), False),
        ]

        self._runTableTests(buffer, tests)


    def testCanIdentifyAsMethodArgument(self):
        buffer = ['func (var *type) yyy(', 'a int, bla string,', ')']

        tests = [
            ((1, 1), True),
            ((1, 9), True),
        ]

        self._runTableTests(buffer, tests)


    def _runTableTests(self, buffer, tests):
        for test in tests:
            self.assertEquals(
                (test[0], test[1]),
                (test[0], is_func_argument(buffer, ID(test[0]))),
            )


if __name__ == '__main__':
    unittest.main()
