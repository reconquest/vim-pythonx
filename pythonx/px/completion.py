# coding=utf8

import re

import px.syntax

from px.identifiers import Identifier


class IdentifierCompleter(object):
    @staticmethod
    def _default_skipper(identifier):
        return px.syntax.get_name(identifier.position) != '' or \
            px.syntax.is_string(identifier.position)

    @staticmethod
    def _default_identifier_matcher(line_number, line):
        matches = re.search('([\w.]+)(?![\w.]*\()$', line)
        if not matches:
            return None

        return Identifier(
            matches.group(1),
            (line_number, matches.start(1) + 1)
        )

    def __init__(self,
            identifiers_re=r'([\w.]+)(?=[\w., ]*:?=)|(\w+)(?=\s+\S+[,)])'):
        self._identifiers_re = identifiers_re

        self._skipper = IdentifierCompleter._default_skipper

        self._identifier_extractor = px.identifiers._default_extractor
        self._identifier_matcher = self._default_identifier_matcher

        self.reset()

    def should_reset(self, cursor):
        if not self._start_position:
            if self._completion:
                return True
            else:
                return False

        completed_cursor_position = (
            self._start_position[0],
            self._start_position[1] + len(self._completion.name),
        )

        if cursor == completed_cursor_position:
            return False
        else:
            return True

    def reset(self):
        self._current_prefix = ''
        self._start_position = None
        self._completion = None
        self._buffer = None

    def get_completion(self):
        return self._completion

    def set_identifier_extractor(self, matcher):
        self._identifier_extractor = matcher

    def get_identifier_completion(
        self,
        buffer,
        cursor,
        identifiers=[],
        should_skip=_default_skipper
    ):
        identifier = px.identifiers.get_under_cursor(
            buffer, cursor, self._identifier_matcher,
        )

        if self._buffer != buffer.number:
            self._completion = None
            self._buffer = None

        if not identifiers:
            search_start = cursor
            if self._completion:
                search_start = self._completion.position

            identifiers = px.identifiers.extract_possible_backward(
                buffer, search_start, self._identifier_extractor,
            )

        if self._completion:
            should_skip = self._make_current_skipper(should_skip)

        new_identifier = px.identifiers.get_last_used(
            identifiers,
            self._completion,
            should_skip
        )

        if not new_identifier:
            return identifier, None

        self._completion = new_identifier
        self._buffer = buffer.number

        return identifier, new_identifier

    def complete_identifier(
        self,
        buffer,
        cursor,
        identifiers=[],
        should_skip=None
    ):
        identifier, new_identifier = self.get_identifier_completion(
            buffer,
            cursor,
            identifiers,
            should_skip,
        )

        line_number, column_number = cursor

        if identifier:
            self._start_position = (
                line_number,
                column_number - len(identifier.name)
            )

        if not new_identifier:
            return None, cursor

        line = buffer[line_number]

        if column_number - len(identifier.name) >= 0:
            buffer[line_number] = line[:column_number-len(identifier.name)]
        else:
            buffer[line_number] = ""

        buffer[line_number] += new_identifier.name + line[column_number:]

        new_cursor = (
            self._start_position[0],
            self._start_position[1] + len(new_identifier.name)
        )

        return new_identifier, new_cursor

    def _make_current_skipper(self, skipper):
        def current_skipper(identifier):
            if skipper(identifier):
                return True

            if re.match(self._completion.name, identifier.name):
                return True
            else:
                return False

        return current_skipper
