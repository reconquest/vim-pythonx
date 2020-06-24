# coding=utf8

import re


def ensure_newlines(buffer, cursor, amount):
    line_number, _ = cursor

    for line in reversed(buffer[:line_number]):
        if line != '':
            break

        if amount <= 0:
            break

        amount -= 1
        line_number -= 1

    buffer[line_number:line_number] = [''] * amount

    return buffer, line_number, amount


def ensure_indent(buffer, cursor, indent,
        expand_tab=True, shift_width=4):
    if expand_tab:
        indent_symbol = ' ' * shift_width
    else:
        indent_symbol = '\t'

    buffer[cursor[0]] = indent_symbol * indent

    return (cursor[0], len(buffer[cursor[0]]))


def get_indentation(line):
    indent = len(line) - len(line.lstrip())

    return indent, line[:indent]


def get_higher_indent(buffer, cursor, current_indent=None):
    line_number, _ = cursor

    if current_indent is None:
        current_indent, _ = get_indentation(buffer[line_number])

    for line in reversed(buffer[:line_number]):
        line_number -= 1
        if line == '':
            continue

        line_indent, _ = get_indentation(line)
        ## return usecase.Update(ctx, userID, map[string]interface{}{
        ##  "buildingID": <- cursor here
        ## }
        if current_indent > line_indent:
        # if current_indent < line_indent:
            return (line, line_number)

    return None


def match_higher_indent(buffer, cursor, pattern):
    line_number, _ = cursor
    current_indent, _ = get_indentation(buffer[line_number])
    indent = get_higher_indent(buffer, (line_number, 0), current_indent)
    if not indent:
        return

    line, line_number = indent
    if re.search(pattern, line.strip()):
        return indent


def match_exact_indent(buffer, cursor, amount, pattern, direction=+1):
    line_number, _ = cursor

    line_number += direction

    while 0 <= line_number < len(buffer):
        line = buffer[line_number]
        line_indent, _ = get_indentation(line)

        if line_indent == amount:
            if re.search(pattern, line):
                return (line_number, 0)
        if line_indent < amount:
            return None

        line_number += direction

    return None


def match_exact_indent_as_in_line(buffer, cursor, line, pattern, direction=+1):
    amount = len(get_indentation(line)[1])
    return match_exact_indent(buffer, cursor, amount, pattern, direction)
