# coding=utf8
import re

import px.completion
import px.buffer

class UnUsedIdentifierCompleter(DefaultCompleter):
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
