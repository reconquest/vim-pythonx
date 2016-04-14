# coding=utf8

import px.common
import px.buffer
import px.autocommands


def complete_identifier_for_placeholder(
    cursor,
    current_value,
    completer=None
):
    if completer is None:
        completer = px.common.wrap_for_filetype(
            'get_identifier_completion'
        )

    cursor = (cursor[0], cursor[1] + len(current_value))

    if current_value != '':
        expect_cursor_jump(cursor)
        px.common.run_cursor_moved_callbacks()

        return current_value
    else:
        px.autocommands.disable_identifier_completion_auto_reset()
        px.autocommands.disable_higlight_auto_clear()

        _, new_identifier = completer()

        if new_identifier:
            return new_identifier.name
        else:
            return ''


def expect_cursor_jump(cursor):
    px.common.register_cursor_moved_callback(
        'complete_identifier_for_placeholder',
        cursor,
        _highlight_completion
    )


def _highlight_completion():
    px.autocommands.enable_highlight_auto_clear()
    px.common.highlight_completion()

