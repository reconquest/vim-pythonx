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
        return []

    names = []
    for syn_id in syntax_stack:
        names.append(
            vim.eval('synIDattr(synIDtrans({}), "name")'.format(syn_id))
        )

    return names


def is_string(cursor):
    return 'String' in get_names(cursor) or is_comment(cursor)


def is_comment(cursor):
    return 'Comment' in get_names(cursor)
