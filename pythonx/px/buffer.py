# coding=utf8

import vim

import px.cursor


def get():
    return vim.current.buffer


def get_before_cursor(buffer, cursor):
    line_number, _ = cursor

    return '\n'.join(buffer[:line_number-1])


def get_pair_line(buffer, line, column):
    old_pos = px.cursor.get()

    px.cursor.set(line + 1, column)

    vim.command("normal %")

    pair_line = get()[px.cursor.get_column() - 1]

    px.cursor.set(old_pos)

    return pair_line


def get_next_nonempty_line(buffer, cursor_line):
    cursor_line += 1
    for line in buffer[cursor_line:]:
        if line.strip() == "":
            cursor_line += 1
            continue

        return line, cursor_line

    return "", 0


def get_prev_nonempty_line(buffer, cursor_line):
    for line in reversed(buffer[:cursor_line]):
        if line.strip() == "":
            continue

        return line

    return ""


def insert_lines_before(buffer, cursor, lines):
    buffer[cursor[0]:cursor[0]] = lines
