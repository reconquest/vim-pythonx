# coding=utf8

import vim
import re
import os
import subprocess
import glob

import util

PHP_SYNTAX_ITEMS = [
    'String',
    'Keyword',
    'Conditional',
    'Number',
    'Type',
]

def get_class_name_with_underscored_namespaces(path=""):
    """ Returns a class name with expanded namespaces from path variable """
    if not path:
        path = vim.eval('expand("%p")')

    path = path.replace('.php', '')
    class_name = re.sub(r'(?!^)\/([a-zA-Z])', lambda m: '_' + m.group(1).upper(), path)
    return class_name

def cycle_by_var_name(identifiers=[]):
    line_number, column_number = vim.current.window.cursor

    identifier = get_identifier_under_cursor()
    new_identifier_data = get_last_used_var(identifier, identifiers)

    if not new_identifier_data:
        return

    (new_identifier, new_identifier_line, new_identifier_column) = \
        new_identifier_data

    buffer = vim.current.window.buffer
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

    util.highlight(
        new_identifier_line,
        new_identifier_column,
        len(new_identifier)
    )

    return new_identifier

def get_all_last_used_identifiers():
    search_space = util.get_buffer_before_cursor()
    line_number, _ = vim.current.window.cursor
    identifiers = []

    for line in reversed(search_space.split('\n')):
        line_number -= 1
        matches = re.finditer(r'(protected|public|private|var)?\s?(\$[\w_\->]+)(?![\w]*\()', line)

        if not matches:
            continue

        for match in reversed(list(matches)):
            is_class_member = match.groups(0)[0]
            identifier = match.groups(0)[1]

            if is_class_member:
                identifiers.append(('$this->' + identifier[1:], line_number,
                    match.start(2)+1))
            else:
                identifiers.append((identifier, line_number, match.start(2)+1))

    return identifiers

def get_identifier_from_string(string, with_dollar=True):
    matches = re.search('(\$[\w_\->]+)', string)

    if not matches:
        return ""

    result = matches.group(1)

    if with_dollar == False and result[0] == '$':
        result = result[1:]

    return result

def get_identifier_under_cursor(with_dollar=True):
    line_number, column_number = vim.current.window.cursor
    line = vim.current.window.buffer[line_number-1][:column_number]

    matches = re.search('(\$[\w_\->]+)$', line)

    if not matches:
        return ""

    result = matches.group(1)

    if with_dollar == False and result[0] == '$':
        result = result[1:]

    return result

def smart_convert_to_camelcase(identifier):
    """
    Smart converting variables to camelCase names.
    """
    if identifier[0] == '_':
        identifier = identifier[1:]

    identifier = identifier[:1].capitalize() + identifier[1:]

    return identifier

def get_camelcase_identifier_from_string(string, with_dollar=True):
    """
    Returns camelCase identifier from string, for example:
    `protected $_storage;`
    returns just `Storage`
    """
    return smart_convert_to_camelcase(get_identifier_from_string(string, with_dollar))

def get_last_used_var(prev_var='', identifiers=[]):
    if not identifiers:
        identifiers = get_all_last_used_identifiers()

    if prev_var:
        prev_var_match_found = False
    else:
        prev_var_match_found = True

    walked = {'$this': True}
    for identifier_data in identifiers:
        (identifier, line, column) = identifier_data

        syntax_name = util.get_syntax_name(line, column)

        if (syntax_name in PHP_SYNTAX_ITEMS):
            continue

        if identifier in walked:
            continue

        if prev_var and identifier.startswith(prev_var):
            if prev_var != identifier:
                return identifier_data

        if prev_var_match_found:
            return identifier_data

        walked[identifier] = True

        if (prev_var == identifier):
            prev_var_match_found = True

def get_phpdoc_variables_before_cursor():
    """
    Returns key-value data from phpdoc before current cursor position.
    Sometimes value may be array
    """
    line_number, _ = vim.current.window.cursor
    buffer = vim.current.window.buffer

    variables = {}
    i = 0
    while i < 10:
        i = i + 1
        line = buffer[line_number-i]
        matches = re.search('\* \@([\w]+) (.*)', line)
        if not matches:
            continue

        name = matches.group(1)
        value = matches.group(2)

        if name in variables:
            if isinstance(variables[name], list):
                variables[name].insert(0, value)
            else:
                variables[name] = [variables[name], value]
        else:
            variables[name] = value

    return variables
