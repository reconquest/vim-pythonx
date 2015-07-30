# coding=utf8

import re
import vim
import util
import importlib
import highlight

IDENTIFIERS_RE = r'([\w.]+)(?=[\w., ]*:?=)|(\w+)(?=\s+\S+[,)])'
COMPLETE_VAR_STATE=''


def reset_complete_var_state():
    global COMPLETE_VAR_STATE
    COMPLETE_VAR_STATE = ''


def get_buffer_before_cursor():
    cursor = vim.current.window.cursor
    line_number = cursor[0]
    buffer = vim.current.buffer

    return '\n'.join(buffer[:line_number-1])


def filter_rainbow_syntax(syntax_name):
    if re.match(r'level\d+', syntax_name):
        return ''
    else:
        return syntax_name


def get_syntax_name((line, column), filter=filter_rainbow_syntax):
    syntax_name = vim.eval(
        'synIDattr(synIDtrans(synID({}, {}, 1)), "name")'.format(
            line, column
        )
    )

    return filter(syntax_name)


def is_syntax_string(cursor):
    return get_syntax_name(cursor) == 'String'


def convert_camelcase_to_snakecase(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)

    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def get_cword():
    return vim.eval('expand("<cword>")')


def paste(content):
    vim.command('set paste')
    vim.command('normal i' + content)
    vim.command('set nopaste')


def get_pair_line(buffer, line, column):
    old_pos = vim.current.window.cursor
    vim.current.window.cursor = (line+1, column)
    vim.command("normal %")
    pair_line = vim.current.buffer[vim.current.window.cursor[0]-1]
    vim.current.window.cursor = old_pos
    return pair_line


def default_highlight((line, column), string):
    return highlight.highlight(line, column, len(string))


def complete_var(
    identifiers=[],
    pattern='([\w.]+)(?![\w.]*\()',
    extract=lambda m: (m.group(1), m.start(1)),
    should_skip=None,
    highlighting=default_highlight
):
    global COMPLETE_VAR_STATE

    buffer = vim.current.window.buffer
    cursor = vim.current.window.cursor

    identifier_data = util.get_identifier_under_cursor(
        buffer, cursor, pattern + '$', extract
    )

    if not identifiers:
        identifiers = util.get_possible_identifiers(
            buffer, cursor, pattern, extract,
        )
        if identifiers[0] == identifier_data:
            identifiers.pop(0)

    if not should_skip:
        def should_skip(*identifier_data):
            return get_syntax_name(identifier_data[1]) != ''

    previous_match = None
    identifier = ''
    if identifier_data:
        (identifier, _) = identifier_data
        if COMPLETE_VAR_STATE != '':
            if highlight.get():
                previous_match = (identifier, highlight.get()[-1][0])
            else:
                previous_match = identifier_data

    if identifier != '' and COMPLETE_VAR_STATE == '':
        COMPLETE_VAR_STATE = identifier

    if COMPLETE_VAR_STATE != '':
        should_skip_default = should_skip
        should_skip = lambda *id_data: should_skip_default(*id_data) or \
                not re.match(r'^' + COMPLETE_VAR_STATE, id_data[0])

    new_identifier_data = util.get_last_used_var(
        identifiers, previous_match, should_skip
    )

    if not new_identifier_data:
        return

    (new_identifier, new_identifier_position) = \
        new_identifier_data

    line_number, column_number = cursor
    line = buffer[line_number-1]

    if column_number-len(identifier) >= 0:
        buffer[line_number-1] = line[:column_number-len(identifier)]
    else:
        buffer[line_number-1] = ""

    buffer[line_number-1] += new_identifier + line[column_number:]

    vim.current.window.cursor = (
        line_number,
        column_number-len(identifier)+len(new_identifier)
    )

    highlighting(new_identifier_position, new_identifier)

    return new_identifier


def wrap_for_filetype(function_name):
    all_module = module = importlib.import_module('px.all')
    try:
        module = importlib.import_module(
            'px.' + vim.current.buffer.options['filetype']
        )
    except ImportError:
        module = all_module
    try:
        return getattr(module, function_name)
    except AttributeError:
        return getattr(all_module, function_name)


def get_last_defined_var_for_snippet(pattern=IDENTIFIERS_RE):
    identifier_data = util.get_last_used_var(
        identifiers=util.get_defined_identifiers(
            vim.current.window.buffer,
            vim.current.window.cursor,
            pattern
        )
    )

    if identifier_data:
        return identifier_data[0]
    else:
        return ''


def get_last_used_var_for_snippet(
    pattern='([\w.]+)(?![\w.]*\(|[\'"])',
    extract=lambda m: (m.group(1), m.start(1))
):
    identifier_data = util.get_last_used_var(
        identifiers=util.get_possible_identifiers(
            vim.current.window.buffer,
            vim.current.window.cursor,
            pattern,
            extract,
        )
    )

    if identifier_data:
        return identifier_data[0]
    else:
        return ''


def get_buffer_line():
    line, _ = vim.current.window.cursor
    buffer = vim.current.buffer
    return buffer, line


def ensure_newlines(buffer, cursor, amount):
    before, how_much = util.ensure_newlines(buffer, cursor[0], amount)
    buffer[before:before] = [''] * how_much


def ensure_indent(buffer, cursor, indent):
    if vim.eval('&et') == "1":
        indent_symbol = ' ' * int(vim.eval('&sw'))
    else:
        indent_symbol = '\t'

    buffer[cursor[0]] = indent_symbol * indent

    return (cursor[0], len(buffer[cursor[0]]))
