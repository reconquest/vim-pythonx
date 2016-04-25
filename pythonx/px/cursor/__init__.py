# coding=utf8

import re
import vim


def get():
    return from_vim(vim.current.window.cursor)


def set(cursor):
    vim.current.window.cursor = to_vim(cursor)


def get_adjusted():
    (line, column) = get()

    if vim.eval('mode()') != 'i':
        return (line, column + 1)
    else:
        return (line, column)


def to_vim(cursor):
    return (cursor[0] + 1, cursor[1])


def to_vim_lang(cursor):
    return (cursor[0] + 1, cursor[1] + 1)


def from_vim(cursor):
    return (cursor[0] - 1, cursor[1])


def is_between(line, cursor, before, after):
    if not re.search(before, line[:cursor[1]+1]):
        return False

    if not re.search(after, line[cursor[1]:]):
        return False

    return True
