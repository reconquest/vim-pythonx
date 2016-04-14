# coding=utf8

import re

import px.completion
import px.buffer


class NotUsedIdentifierCompleter(px.completion.IdentifierCompleter):
    @staticmethod
    def _default_identifier_extractor(line_number, line):
        buffer = px.buffer.get()

        identifiers = px.identifiers._default_extractor(line_number, line)
        for identifier in identifiers:
            if NotUsedIdentifierCompleter._is_just_assigned(
                buffer, identifier
            ):
                yield identifier

    @staticmethod
    def _is_just_assigned(buffer, identifier):
        if NotUsedIdentifierCompleter._is_passed_by_address(
            buffer, identifier
        ):
            return True

        if NotUsedIdentifierCompleter._is_assigned(
            buffer, identifier
        ):
            return True

        if NotUsedIdentifierCompleter._is_func_argument(
            buffer, identifier
        ):
            return True

        return False

    @staticmethod
    def _is_passed_by_address(buffer, identifier):
        if identifier.position[1] <= 0:
            return False

        if buffer[identifier.position[0]][identifier.position[1]-1] == '&':
            return True
        else:
            return False

    @staticmethod
    def _is_func_argument(
        buffer, identifier,
        should_skip=px.syntax.is_string
    ):
        pairs = {
            '{': '}',
            '(': ')',
        }

        skip_counters = {
            '}': 0,
            ')': 0,
        }

        meet_comma = False

        line_number = identifier.position[0]
        column_number = identifier.position[1] - 1
        test_buffer = ""
        while line_number >= 0:
            if column_number < 0:
                line_number -= 1
                column_number = len(buffer[line_number]) - 1
                continue

            char = buffer[line_number][column_number]

            if char == ',':
                meet_comma = True
            elif re.match(r'\w', char):
                meet_comma = False
            elif char in pairs.values():
                if not should_skip((line_number, column_number)):
                    if not meet_comma:
                        return False
                    skip_counters[char] += 1
            elif char in pairs.keys():
                if not should_skip((line_number, column_number)):
                    if skip_counters[pairs[char]] == 0:
                        if re.search(r'(\W|^)func(\s+\([\w\s*]+\))?\s+\w+\($',
                                buffer[line_number][:column_number+1]):
                            return True
                        else:
                            return False
                    else:
                        skip_counters[pairs[char]] -= 1

            column_number -= 1

        return False

    @staticmethod
    def _is_assigned(buffer, identifier):
        identifier_line = buffer[identifier.position[0]]
        line_after_identifier = identifier_line[identifier.position[1]:]

        if re.match(r'[,\w\s]*:?=', line_after_identifier):
            return True
        else:
            return False

    def __init__(self):
        super(self.__class__, self).__init__()

        self.set_identifier_extractor(self._default_identifier_extractor)
