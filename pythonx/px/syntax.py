# coding=utf8

import re
import vim

import px.cursor


def filter_rainbow(syntax_name):
    if re.match(r'level\d+', syntax_name):
        return ''
    else:
        return syntax_name


def get_name(position, filter=filter_rainbow):
    try:
        syntax_name = vim.eval(
            'synIDattr(synIDtrans(synID({}, {}, 1)), "name")'.format(
                *px.cursor.to_vim_lang(position)
            )
        )
    except:
        return ''

    return filter(syntax_name)


def get_names(position):
    try:
        syntax_stack = vim.eval('synstack({}, {})'.format(
            *px.cursor.to_vim_lang(position)
        ))
    except:
        pass

    names = []
    for syn_id in syntax_stack:
        names.append(
            vim.eval('synIDattr({}, "name")'.format(syn_id))
        )
        names.append(
            vim.eval('synIDattr(synIDtrans({}), "name")'.format(syn_id))
        )

    return names


def is_string(cursor):
    for name in get_names(cursor):
        if 'string' in name.lower():
            return True

    return False


def is_number(cursor):
    for name in get_names(cursor):
        if 'Number' in name:
            return True

    return False

# lookbehind=True will match previous character as well due weird syntax
# identification in vim, when last character in comment is not identified
# as comment.
def is_comment(cursor, lookbehind=True):
    comment = False
    for name in get_names(cursor):
        if 'comment' in name.lower():
            comment = True
            break

    if lookbehind:
        if cursor[1] != 0 and is_comment((cursor[0], cursor[1]-1), False):
            return True

    return comment
