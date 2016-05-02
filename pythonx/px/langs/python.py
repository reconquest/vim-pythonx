# coding=utf8

import vim
import re
import px.whitespaces
import px.buffer

function_re = re.compile('^def ')
method_re = re.compile('^\s+def ')
class_re = re.compile('^class ')


def ensure_newlines(buffer, cursor):
    line_number, _ = cursor
    line = buffer[line_number]
    if function_re.match(line):
        px.whitespaces.ensure_newlines(buffer, (line_number, 0), 2)
    if method_re.match(line):
        px.whitespaces.ensure_newlines(buffer, (line_number, 0), 1)
    if class_re.match(line):
        px.whitespaces.ensure_newlines(buffer, (line_number, 0), 2)


def ensure_newlines_after(buffer, cursor):
    x, line_number = px.buffer.get_next_nonempty_line(buffer, cursor[0])
    if line_number <= 0:
        return
    else:
        ensure_newlines(buffer, (line_number, 0))


def ensure_indent(buffer, cursor, indent):
    if vim.eval('&et') == "1":
        indent_symbol = ' ' * int(vim.eval('&sw'))
    else:
        indent_symbol = '\t'

    buffer[cursor[0]] = indent_symbol * indent

    return (cursor[0], len(buffer[cursor[0]]))
