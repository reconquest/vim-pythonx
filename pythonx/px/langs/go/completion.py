# coding=utf8

import re
import px.completion
import px.buffer


class NotUsedIdentifierCompleter(px.completion.IdentifierCompleter):
    @staticmethod
    def _default_identifier_extractor(line_number, line):
        buffer = px.buffer.get()

        identifiers = px.identifiers._default_extractor(line_number, line)
        not_used_identifiers = []
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
