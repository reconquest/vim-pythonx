# coding=utf8
import re

import px.completion
import px.buffer

from px.langs.go.completion import DefaultCompleter

class UnusedIdentifierCompleter(DefaultCompleter):
    @staticmethod
    def _default_identifier_extractor(line_number, line):
        buffer = px.buffer.get()

        identifiers = px.identifiers._default_extractor(line_number, line)
        for identifier in identifiers:
            if UnusedIdentifierCompleter._is_just_assigned(
                buffer, identifier
            ):
                yield identifier

    @staticmethod
    def _is_just_assigned(buffer, identifier):
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

    def __init__(self):
        super(self.__class__, self).__init__()

        self.set_identifier_extractor(self._default_identifier_extractor)
