# coding=utf8

import px.completion
import px.buffer

from px.langs.go.completion import DefaultCompleter


class UnusedIdentifierCompleter(DefaultCompleter):
    @staticmethod
    def _default_identifier_extractor(line_number, line):
        buffer = px.buffer.get()

        identifiers = DefaultCompleter._default_identifier_extractor(
            line_number,
            line
        )

        try:
            for identifier in identifiers:
                seen = identifier.name in UnusedIdentifierCompleter._seen
                if not seen and UnusedIdentifierCompleter._is_just_assigned(
                    buffer,
                    identifier
                ):
                    yield identifier
                else:
                    UnusedIdentifierCompleter._seen[identifier.name] = True
        except:
            pass

    def reset(self):
        try:
            super(UnusedIdentifierCompleter, self).reset()
        except:
            raise

        UnusedIdentifierCompleter._seen = {}

    @staticmethod
    def _is_just_assigned(buffer, identifier):
        if DefaultCompleter._is_type_name(
            buffer, identifier
        ):
            return False

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
        super(UnusedIdentifierCompleter, self).__init__()

        self._seen = {}
        self.set_identifier_extractor(self._default_identifier_extractor)
