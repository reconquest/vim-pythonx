# coding=utf8

import re


def get_last_used_var(identifiers, previous_match=None, should_skip=None):
    if not should_skip:
        should_skip = lambda *_: False

    if previous_match:
        prev_var_match_found = False
    else:
        prev_var_match_found = True

    walked = {}
    for identifier_data in identifiers:
        (identifier, (line, column)) = identifier_data

        if should_skip(*identifier_data):
            continue

        if identifier in walked:
            continue

        if previous_match and identifier_data == previous_match:
            if previous_match[0] != identifier:
                return identifier_data

        if prev_var_match_found:
            return identifier_data

        walked[identifier] = True

        if previous_match == identifier_data:
            prev_var_match_found = True


def get_identifier_from_string(line, pattern, extract):
    matches = re.search(pattern, line)

    if not matches:
        return ('', 0)

    return extract(matches)


def get_identifier_under_cursor(
    buffer, cursor,
    pattern='([\w.]+)$', extract=lambda m: (m.group(1), m.start(1))
):
    (line_number, column_number) = cursor
    line = buffer[line_number-1][:column_number]
    identifier, start_at = get_identifier_from_string(line, pattern, extract)
    if identifier:
        return (identifier, (line_number, start_at + 1))
    else:
        return None


def get_possible_identifiers(
    buffer, cursor,
    pattern=r'([\w.]+)(?![\w.]*\()',
    extract=lambda m: (m.group(1), m.start(1))
):
    line_number, _ = cursor
    identifiers = []

    for line in reversed(buffer[:line_number]):
        line_number -= 1
        matches = re.finditer(pattern, line)

        if not matches:
            continue

        for match in reversed(list(matches)):
            identifier, start_at = extract(match)
            identifiers.append(
                (identifier, (line_number + 1, start_at + 1))
            )

    return identifiers


def get_defined_identifiers(
    buffer, cursor, pattern
):
    line_number, _ = cursor
    identifiers = []

    for line in reversed(buffer[:line_number-1]):
        line_number -= 1
        matches = re.finditer(pattern, line)

        if not matches:
            continue

        for match in reversed(list(matches)):
            group_id = 1
            if not match.group(group_id):
                group_id = 2
            identifier = match.group(group_id)
            identifiers.append((identifier, (line_number, match.start(group_id)+1)))

    return identifiers



def get_higher_ident(buffer, cursor):
    line_number, _ = cursor

    current_indent = get_indentation(buffer[line_number-1])
    for line in reversed(buffer[:line_number-1]):
        line_number -= 1
        if line == '':
            continue
        line_indent = get_indentation(line)
        if current_indent > line_indent:
            return (line.strip(), line_number)

    return None


def match_higher_indent(buffer, cursor, pattern):
    line_number, _ = cursor
    while True:
        indent = get_higher_ident(buffer, (line_number, 0))
        if not indent:
            return
        line, line_number = indent
        if re.search(pattern, line):
            return indent


def get_indentation(line):
    return len(line) - len(line.lstrip())


def get_prev_nonempty_line(buffer, cursor_line):
    for line in reversed(buffer[:cursor_line-1]):
        if line.strip() == "":
            continue
        return line
    return ""


def ensure_newlines(buffer, line_number, amount):
    for line in reversed(buffer[:line_number]):
        if line != '':
            break

        if amount <= 0:
            break

        amount -= 1
        line_number -= 1

    return line_number, amount
