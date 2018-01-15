# coding=utf8

import vim

import px.common
import px.buffer
import px.autocommands

option_highlight_completion = 1

def _highlight_completion():
    px.autocommands.enable_highlight_auto_clear()
    px.common.highlight_completion()

def complete_identifier_for_placeholder(
    cursor,
    current_value,
    completer=None,
    should_skip=None,
):
    if completer is None:
        completer = px.common.wrap_for_filetype(
            'get_identifier_completion'
        )

    cursor = (cursor[0], cursor[1] + len(current_value))

    if current_value != '':
        if option_highlight_completion == 1:
            expect_cursor_jump(cursor, _highlight_completion)
        px.common.run_cursor_moved_callbacks()

        return current_value
    else:
        px.autocommands.disable_identifier_completion_auto_reset()
        if option_highlight_completion == 1:
            px.autocommands.disable_higlight_auto_clear()

        if should_skip:
            _, new_identifier = completer(should_skip=should_skip)
        else:
            _, new_identifier = completer()

        if new_identifier:
            return new_identifier.name
        else:
            return ''


def expect_cursor_jump(cursor, callback):
    px.common.register_cursor_moved_callback(
        'snippets_cursor_jump',
        cursor,
        callback
    )


def make_context(snip):
    return {'__dummy': None}


def make_jumper(snip, on_tabstop=1):
    if snip.tabstop != on_tabstop:
        return

    snip.context.update({'jumper': {'enabled': True, 'snip': snip}})


def get_jumper_position(snip):
    if not snip.context or 'jumper' not in snip.context:
        return None

    return snip.context['jumper']['snip'].tabstop


def get_jumper_text(snip):
    if not snip.context or 'jumper' not in snip.context:
        return None

    number = get_jumper_position(snip)

    if number not in snip.context['jumper']['snip'].tabstops:
        return None

    return snip.context['jumper']['snip'].tabstops[number].current_text


def advance_jumper(snip):
    return _make_jumper_jump(snip, "forwards")


def rewind_jumper(snip):
    return _make_jumper_jump(snip, "backwards")


def enable_jumper(snip):
    snip.context['jumper']['enable'] = True


def expand(snip, jump_pos=1):
    if snip.tabstop != jump_pos:
        return

    vim.eval('feedkeys("\<C-R>=UltiSnips#ExpandSnippet()\<CR>")')


def _make_jumper_jump(snip, direction):
    if not snip.context or 'jumper' not in snip.context:
        return False

    jumper = snip.context['jumper']
    if not jumper['enabled']:
        return False

    jumper['enabled'] = False

    vim.command('call feedkeys("\<C-R>=UltiSnips#Jump' +
        direction.title() + '()\<CR>")')

    return True
