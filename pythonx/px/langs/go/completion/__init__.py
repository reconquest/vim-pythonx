# coding=utf8

import re

import px.completion
import px.buffer


class DefaultCompleter(px.completion.IdentifierCompleter):
    @staticmethod
    def _default_identifier_extractor(line_number, line):
        buffer = px.buffer.get()

        identifiers = px.identifiers._default_extractor(line_number, line)
        for identifier in identifiers:
            if not DefaultCompleter._is_struct_instantiation(
                buffer,
                identifier
            ):
                yield identifier

    @staticmethod
    def _default_skipper(identifier):
        if identifier.name == '_':
            return True
        else:
            if px.syntax.get_name(identifier.position) in ['goErr']:
                return False

            return px.completion.IdentifierCompleter._default_skipper(
                identifier
            )

    @staticmethod
    def _is_just_assigned(buffer, identifier):
        if DefaultCompleter._is_type_name(
            buffer, identifier
        ):
            return False

        if DefaultCompleter._is_passed_by_address(
            buffer, identifier
        ):
            return True

        if DefaultCompleter._is_assigned(
            buffer, identifier
        ):
            return True

        if DefaultCompleter._is_func_argument(
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
    def _is_struct_instantiation(buffer, identifier):
        offset = identifier.position[1]+len(identifier.name)
        if offset >= len(buffer[identifier.position[0]]):
            return False

        if buffer[identifier.position[0]][offset] == '{':
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
                        if re.search(
                            r'(\W|^)func(\s+\([\w\s*]+\))?(\s+\w+)?\($',
                            buffer[line_number][:column_number+1]
                        ):
                            return True
                        else:
                            return False
                    else:
                        skip_counters[pairs[char]] -= 1

            column_number -= 1

        return False

    @staticmethod
    def _is_type_name(buffer, identifier):
        position = identifier.position
        before_identifier = buffer[position[0]][:position[1]]

        if re.match(r'.*\w+\s+\*?', before_identifier):
            return True
        else:
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
        super(DefaultCompleter, self).__init__()

        self.set_identifier_extractor(self._default_identifier_extractor)
