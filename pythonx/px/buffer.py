# coding=utf8

import vim

import px.cursor


def get():
    return vim.current.buffer


def get_before_cursor(buffer, cursor):
    line_number, _ = cursor

    return '\n'.join(buffer[:line_number-1])


def get_pair_line(buffer, line, column):
    if line+1 >= len(buffer):
        return get()[line]

    old_pos = px.cursor.get()

    px.cursor.set((line, column))

    vim.command("normal %")

    pair_line = get()[px.cursor.get()[0]]

    px.cursor.set(old_pos)

    return pair_line


def get_next_nonempty_line(buffer, cursor):
    cursor += 1
    for line in buffer[cursor:]:
        if line.strip() == "":
            cursor += 1
            continue

        return line, cursor

    return "", 0


def get_prev_nonempty_line(buffer=None, cursor=None):
    if not buffer:
        buffer = get()
    if not cursor:
        cursor, _ = px.cursor.get()

    for line in reversed(buffer[:cursor]):
        if line.strip() == "":
            continue

        return line

    return ""


def insert_lines_before(buffer, cursor, lines):
    buffer[cursor[0]:cursor[0]] = lines


def get_current_line():
    buffer = get()
    cursor, _ = px.cursor.get()
    return buffer[cursor]

def get_current_line_before_cursor():
    buffer = get()
    (line, column) = px.cursor.get()

    return buffer[line][:column]
