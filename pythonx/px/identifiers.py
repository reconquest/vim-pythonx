# coding=utf8

import re
import collections
import types

Identifier = collections.namedtuple('Identifier', ['name', 'position'])


def _no_skip(*_):
    return False


def get_last_used(identifiers, previous_match=None,
        should_skip=_no_skip, walked={}):
    for identifier in identifiers:
        if isinstance(identifier, types.GeneratorType):
            result = get_last_used(identifier, previous_match, should_skip, walked)
            if result:
                return result
        else:
            if should_skip(identifier):
                continue

            if identifier in walked:
                continue

            walked[identifier.name] = True

            if previous_match:
                if previous_match.name == identifier.name:
                    continue

            return identifier

def _default_under_cursor_matcher(line_number, line):
    matches = re.search('([\w.]+)$', line)
    if not matches:
        return None

    return Identifier(
        matches.group(1),
        (line_number, matches.start(1))
    )


def get_under_cursor(
    buffer, cursor,
    matcher=_default_under_cursor_matcher,
):
    line_number, column_number = cursor

    line = buffer[line_number][:column_number]

    identifier = matcher(line_number, line)
    if not identifier:
        return Identifier('', cursor)
    else:
        return identifier


def _default_extractor(line_number, line):
    matches = re.finditer('([\w.]+)(?![\w.]*\()', line)
    if not matches:
        return

    for match in reversed(list(matches)):
        yield Identifier(
            match.group(1),
            (line_number, match.start(1))
        )


def extract_possible_backward(
    buffer, cursor,
    extractor=_default_extractor,
    cutoff=50,
):
    line_number, column_number = cursor

    identifiers = []
    if column_number > 0 and line_number >= 0:
        identifiers += [extractor(
            line_number,
            buffer[line_number][:column_number]
        )]

    while line_number > 0:
        line_number -= 1
        cutoff -= 1

        if cutoff < 0:
            break

        line = buffer[line_number]

        identifiers += [extractor(line_number, line)]

    return identifiers
