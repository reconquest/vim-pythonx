# coding=utf8

import vim
import re
import subprocess

import px.common
import px.cursor
import px.identifiers
import px.buffer
import px.syntax

import completion

from autoimport import Autoimporter
from completion import DefaultCompleter
from completion.unused import UnusedIdentifierCompleter


GOROOT = subprocess.check_output(['go', 'env', 'GOROOT']).strip()
GOPATH = subprocess.check_output(['go', 'env', 'GOPATH']).strip()

_DefaultAutoimporter = Autoimporter()
_DefaultCompleter = DefaultCompleter()

_UnusedIdentifierCompleter = UnusedIdentifierCompleter()


def extract_prev_method_binding(buffer, cursor):
    search_space = px.buffer.get_before_cursor(buffer, cursor)

    def extract_from_type_definition():
        matches = re.findall(r'(?m)^type (\w+) ', search_space)

        if matches != []:
            type_name = matches[-1]
            object_name = re.findall(r'(\w[^A-Z]+)', type_name)[-1].lower()

            return (object_name, type_name)
        else:
            return None

    def extract_from_method_definition():
        matches = re.findall(
            r'(?m)^func \(([^)]+)\s+\*?([^)]+)\) ',
            search_space
        )

        if matches != []:
            return matches[-1]
        else:
            return None

    result = extract_from_method_definition()
    if result is None:
        result = extract_from_type_definition()

    return result


def get_previous_slice_usage(buffer, cursor):
    search_space = px.buffer.get_before_cursor(buffer, cursor)
    matches = re.findall(r'(\w+)\[', search_space)

    if matches:
        return matches[-1]

    return ""


def split_parenthesis():
    first_paren = vim.eval('searchpos("(", "bc")')
    vim.command('exec "normal a\<CR>"')
    vim.command('call search("(", "bc")')
    px.cursor.set((int(first_paren[0])-1, int(first_paren[1])))
    vim.command('normal %')
    vim.command('exec "normal ha,\<CR>"')


def is_if_bracket(buffer, line, column):
    return px.buffer.get_pair_line(buffer, line, column).strip().startswith(
        "if"
    )


def is_return_argument(buffer, line, column):
    return buffer[line].strip().startswith('return ')


def is_in_err_condition(buffer, line, column):
    prev_line = buffer[line-1]
    if re.search('^if .*err != nil', prev_line.strip()):
        return buffer[line].strip().startswith('return ')
    else:
        return False


def is_struct_bracket(buffer, line, column):
    is_struct_def = re.match("^type \w+ struct",
        px.buffer.get_pair_line(buffer, line, column))

    is_method_def = re.match("^func \(\w+ \w+\) ",
        px.buffer.get_pair_line(buffer, line, column))

    return is_struct_def or is_method_def


def get_bracket_line(buffer, line):
    while True:
        line_contents = buffer[line]
        if re.search(' {$', line_contents):
                return line

        if line == 0:
                return False

        line = line - 1


def is_type_declaration(buffer, line):
    bracket_line = get_bracket_line(buffer, line)
    if not bracket_line:
            return False

    bracket_line_contents = buffer[bracket_line]
    if bracket_line_contents.strip().startswith('type '):
            return True
    else:
            return False


def is_switch(buffer, line):
    bracket_line = get_bracket_line(buffer, line)
    if not bracket_line:
            return False

    bracket_line_contents = buffer[bracket_line]
    if bracket_line_contents.strip().startswith('switch '):
            return True
    else:
            return False


def is_func_declaration(buffer, line):
    current_line = line

    while True:
        line_contents = buffer[line]

        bracket = False
        if re.search(' {$', line_contents):
            bracket = True

        func = False
        if line_contents.strip().startswith('func '):
            func = True

        if bracket:
            if func and line == current_line:
                    return True
            else:
                return False
        else:
            if func:
                return True

        if line == 0:
            return False

        line = line - 1

    return False


const_re = re.compile('^const ')
type_re = re.compile('^type ')
var_re = re.compile('^var ')
func_re = re.compile('^func ')


def goto_re(regexp):
    line_number = 0
    for line in px.buffer.get():
        line_number += 1

        if regexp.match(line):
            px.cursor.set((line_number, 0))
            return True

    return False


def goto_re_first_before_cursor(regexp):
    line_number, column_number = px.cursor.get()

    while True:
        line = buffer[line_number - 1]
        if regexp.match(line.strip()):
            px.cursor.set((line_number, 0))

        line_number -= 1
        if line_number == 1:
            return False

    return False


def goto_const():
    return goto_re(const_re) or goto_re(func_re)


def goto_type():
    return goto_re(type_re) or goto_re(func_re)


def goto_var():
    return goto_re(var_re) or goto_re(func_re)


def goto_prev_var():
    return goto_re_first_before_cursor(var_re)


def is_before_first_func(buffer, line):
    line_iter = 0
    while line_iter <= line:
        if buffer[line_iter][:5] == 'func ':
            return False

        line_iter += 1

    return True


def get_gocode_complete(full=True):
    info = gocode_get_info()
    if not info:
        return ""

    cursor = px.cursor.get()
    buffer = px.buffer.get()

    line_till_cursor =  buffer[cursor[0]][:cursor[1]]
    function_name = re.search(r'\w+\.\w+$', line_till_cursor).group(0)

    # removing 'func '
    info = info[5:]

    if info[-1] == ')' and len(info.rsplit(') (', 2)) == 2:
        body_func, body_return = info.rsplit(') (', 2)
        _, body_args_func = body_func.split('(', 2)

        # removing last ')'
        body_return = body_return[:-1]
    else:
        body_func, body_return = info.rsplit(')', 2)
        _, body_args_func = body_func.split('(', 2)

    args_func = body_args_func.strip().split(', ')

    placeholder = 1

    returns_exists = body_return != ""
    if returns_exists:
        args_return = body_return.strip().split(', ')

        snippet_return_parts = []
        for arg in args_return:
            snippet_return_parts.append(
                '${' + str(placeholder) + ':' + arg + '}'
            )
            placeholder += 1

        snippet_return = ', '.join(snippet_return_parts)

    if not full:
        placeholder = 1

    snippet_func_parts = []
    for arg in args_func:
        snippet_func_parts.append('${' + str(placeholder) + ':' + arg + '}')
        placeholder += 1

    snippet_func = function_name + '(' + ', '.join(snippet_func_parts) + ')'

    if not full:
        if returns_exists:
            return (snippet_return, snippet_func)
        return ("", snippet_func)

    if returns_exists:
        snippet = snippet_return + ' := ' + snippet_func
    else:
        snippet = snippet_func

    return snippet


def gocode_can_complete():
    info = gocode_get_info()
    if not info:
        return False

    return True


def gocode_get_info():
    line, column = px.cursor.get()

    px.cursor.set((line, column - 1))
    info = vim.eval('go#complete#GetInfo()')
    px.cursor.set((line, column))

    return info


def autoimport_at_cursor():
    _DefaultAutoimporter.autoimport_at_cursor()


def get_not_used_identifier_completion(
    identifiers=[],
    should_skip=UnusedIdentifierCompleter._default_skipper
):
    px.common.set_active_completer(_UnusedIdentifierCompleter)

    return _UnusedIdentifierCompleter.get_identifier_completion(
        px.buffer.get(),
        px.cursor.get(),
        identifiers,
        should_skip
    )
