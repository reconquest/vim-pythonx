#06-Jan-2020     coding=utf8

import vim
import re
import subprocess

import px.common
import px.cursor
import px.identifiers
import px.buffer
import px.syntax
import px.whitespaces

from px.langs.go.autoimport import Autoimporter
from px.langs.go.completion import DefaultCompleter
from px.langs.go.completion.unused import UnusedIdentifierCompleter
from px.langs import goto_re
from px.langs import goto_re_first_before_cursor


GOROOT = subprocess.check_output(['go', 'env', 'GOROOT'], encoding='UTF-8').strip()
GOPATH = subprocess.check_output(['go', 'env', 'GOPATH'], encoding='UTF-8').strip()

_DefaultAutoimporter = Autoimporter()
_DefaultCompleter = DefaultCompleter()

_UnusedIdentifierCompleter = UnusedIdentifierCompleter()


def extract_prev_method_binding(buffer, cursor):
    search_space = px.buffer.get_before_cursor(buffer, cursor)

    def extract_from_type_definition(line):
        matches = re.findall(r'(?m)^type (\w+) ', line)

        if matches != []:
            type_name = matches[-1]
            object_name = re.findall(
                r'(\w[^A-Z]+|[A-Z_-]+)',
                type_name
            )[-1].lower()

            return (object_name, type_name)
        else:
            return None

    def extract_from_method_definition(line):
        matches = re.findall(
            r'(?m)^func \(([^)]+)\s+\*?([^)]+)\) ',
            line
        )

        if matches != []:
            return matches[-1]
        else:
            return None

    result = None
    for line in reversed(search_space.split('\n')):
        result = extract_from_method_definition(line)
        if result is None:
            result = extract_from_type_definition(line)
        if result:
            break

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
    bracket_pos = px.whitespaces.match_higher_indent(
        buffer,
        (line, None),
        ' {$',
    )

    if bracket_pos is None:
        return False

    return bracket_pos[1]


def is_type_declaration(buffer, line):
    bracket_line = get_bracket_line(buffer, line)
    if not bracket_line:
            return False

    bracket_line_contents = buffer[bracket_line]
    if bracket_line_contents.strip().startswith('type '):
            return True
    elif bracket_line_contents.strip().endswith('struct {'):
            return True
    else:
            return False


def is_switch(buffer, line):
    match = px.whitespaces.match_exact_indent_as_in_line(
        buffer,
        (line, None),
        buffer[line],
        '^\s*switch ',
        direction=-1
    )

    if match is not None:
        return True
    else:
        return False

def is_case(buffer, line):
    match = px.whitespaces.match_higher_indent(
        buffer,
        (line, None),
        '^\s*(case\s+|default:)'
    )

    if match is not None:
        return True
    else:
        return False


def is_select(buffer, line):
    match = px.whitespaces.match_exact_indent_as_in_line(
        buffer,
        (line, None),
        buffer[line],
        '^\s*select ',
        direction=-1
    )

    if match is not None:
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
package_re = re.compile('^package ')



def goto_const():
    return goto_re(const_re) or goto_re(package_re) or goto_re(func_re)


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
    info = gocode_get_info("")
    if not info:
        return ""

    cursor = px.cursor.get()
    buffer = px.buffer.get()

    line_till_cursor = buffer[cursor[0]][:cursor[1]]
    function_name = re.search(r'\w+\.\w+$', line_till_cursor).group(0)

    is_type_func = False
    if re.match(r'type \w+ func', info):
        is_type_func = True
        info = re.sub(r'^type \w+ ', '', info)
    else:
        # removing 'func '
        info = info[5:]

    if info[-1] == ')' and len(info.rsplit(') (', 1)) == 2:
        body_func, body_return = info.rsplit(') (', 1)
        _, body_args_func = body_func.split('(', 1)

        # removing last ')'
        body_return = body_return[:-1]
    else:
        body_func, body_return = info.rsplit(')', 1)
        _, body_args_func = body_func.split('(', 1)

    args_func = body_args_func.strip().split(', ')

    placeholder = 1

    returns_many = False

    returns_exists = body_return != ""
    if returns_exists:
        args_return = body_return.strip().split(', ')
        if len(args_return) > 1:
            returns_many = True

        snippet_return_parts = []
        for arg in args_return:
            snippet_return_parts.append(
                '${' + str(placeholder) + ':' + arg + '}'
            )
            placeholder += 1

        snippet_return = ', '.join(snippet_return_parts)

    # XXX: what is it for?
    # if not full:
    #     placeholder = 1

    snippet_func_parts = []
    for arg in args_func:
        if is_type_func:
            var, type = arg.split(' ', 2)
            snippet_func_parts.append('${' + str(placeholder) + ':' +var+ '} ' + type)
        else:
            snippet_func_parts.append('${' + str(placeholder) + ':' + arg + '}')

        placeholder += 1

    if is_type_func:
        function_name = 'func'

    snippet_func = function_name + '(' + ', '.join(snippet_func_parts) + ')'

    if is_type_func:
        snippet_return = '${' + str(placeholder) + ':function}'
        snippet_func += ' ' + body_return.strip()
        if returns_many:
            snippet_func += '(' + snip_func + ')'
        snippet_func += ' {\n\t${0}\n}'

    if not full:
        if returns_exists:
            return (snippet_return, snippet_func)
        return ("", snippet_func)

    if returns_exists:
        snippet = snippet_return + ' := ' + snippet_func
    else:
        snippet = snippet_func

    return snippet


def get_package_path():
    return vim.eval("px#go#GetPackagePath()")


def gocode_can_complete():
    info = gocode_get_info("")
    if not info:
        return False

    return True


def gocode_get_info(identifier):
    line, column = px.cursor.get()

    if identifier != "":
        info = vim.eval("px#go#get_info('"+identifier+"')")
        return info

    before = px.buffer.get()[line][:column]
    word = re.search(r'(\w+)*$', before).group(1)

    info = vim.eval("px#go#get_info('" + word + "')")

    return info


def autoimport_at_cursor():
    _DefaultAutoimporter.autoimport_at_cursor()


def autoimport_reset_cache():
    _DefaultAutoimporter.reset()


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
