# coding=utf8

import vim
import re
import os
import subprocess
import glob

import util
import all

GOROOT = subprocess.check_output(['go', 'env', 'GOROOT']).strip()
GOPATH = subprocess.check_output(['go', 'env', 'GOPATH']).strip()

GO_SYNTAX_ITEMS = [
    'String',
    'Keyword',
    'Repeat',
    'Conditional',
    'Number',
    'Statement',
    'Type',
]

_imports_cache = {}

def extract_prev_method_binding_for_cursor():
    search_space = all.get_buffer_before_cursor()

    def extract_from_type_definition():
        matches = re.findall(r'(?m)^type (\w+) ', search_space)

        if matches != []:
            type_name = matches[-1]
            object_name = re.findall(r'(\w[^A-Z]+)', type_name)[-1].lower()

            return (object_name, type_name)
        else:
            return None

    def extract_from_method_definition():
        matches = re.findall(r'(?m)^func \(([^)]+)\s+\*?([^)]+)\) ', search_space)

        if matches != []:
            return matches[-1]
        else:
            return None

    result = extract_from_method_definition()
    if result is None:
        result = extract_from_type_definition()

    return result


def guess_package_name_from_file_name(path):
    basename = os.path.basename(os.path.dirname(os.path.abspath(path)))

    if re.match(r'^\w+$', basename):
        return basename
    else:
        return 'main'


def get_previous_slice_usage():
    search_space = all.get_buffer_before_cursor()
    matches = re.findall(r'(\w+)\[', search_space)

    if matches:
        return matches[-1]

    return ""


def split_parenthesis():
    line_number, column_number = vim.current.window.cursor
    buffer = vim.current.buffer
    line = buffer[line_number-1]
    first_parenthesis = line.rfind('(', 0, column_number)
    last_parenthesis = line.rfind(')')
    indent = len(line) - len(line.lstrip("\t"))

    buffer[line_number:line_number]= [
        "\t" * (indent + 1) + line[first_parenthesis+1:last_parenthesis] + ",",
        "\t" * indent + line[last_parenthesis:],
        "",
    ]

    buffer[line_number-1] = line[:first_parenthesis+1]


def get_imports():
    buffer = vim.current.buffer
    reImportLine = r'\s* ((\w+) \s+)? "([^"]+)" \s*'

    matches = re.findall(r"""
        (?sxm)
        import \s* \(?(
            (""" + reImportLine + """)+
        )\)?""", "\n".join(buffer))

    if not matches:
        return []

    matches = re.findall(r"(?sxm)" + reImportLine, matches[0][0])
    if not matches:
        return[]

    result = []
    for match in matches:
        if not match[1]:
            package_name = path_to_import_name(match[2])
        else:
            package_name = match[1]
        result.append((package_name, match[2]))

    return result


def path_to_import_name(path):
    gopath = GOROOT + ":" + GOPATH

    for lib_path in gopath.split(':'):
        gofiles = glob.glob(os.path.join(lib_path, "src", path, "*.go"))

        if not gofiles:
            continue

        for gofile in gofiles:
            package_name = get_package_name_from_file(gofile)

            if package_name:
                return package_name


def get_package_name_from_file(path):
    with open(path) as gofile:
        for line in gofile:
            if line.endswith('_test\n'):
                continue
            if line.startswith('package '):
                return line.split(' ')[1].strip()


def is_if_bracket(buffer, line, column):
    return all.get_pair_line(buffer, line, column).strip().startswith("if")


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
        all.get_pair_line(buffer, line, column))
    is_method_def = re.match("^func \(\w+ \w+\) ",
        all.get_pair_line(buffer, line, column))
    return is_struct_def or is_method_def


def autoimport():
    info = vim.eval('go#complete#GetInfo()')
    if info != "" and re.match("^var \w+", info):
        return

    identifier_data = util.get_identifier_under_cursor(
        vim.current.buffer,
        vim.current.window.cursor,
    )

    if not identifier_data:
        return

    identifier, _ = identifier_data

    if identifier.count('.') > 1:
        return

    possible_package = identifier.split('.')[0]
    import_path = get_import_path_for_identifier(possible_package)
    if not import_path:
        return

    vim.command('GoImport {}'.format(import_path))


def get_import_path_for_identifier(identifier):
    imports = get_all_imports()
    if identifier not in imports:
        return None
    return imports[identifier]


# @TODO: create cache function wrapper
def get_all_imports():
    global _imports_cache

    if _imports_cache:
        return _imports_cache

    gopath = GOROOT + ":" + GOPATH

    _imports_cache = {}

    for lib_path in gopath.split(':'):
        src_dir = os.path.join(lib_path, "src")
        gofile = None
        last_package_path = None
        for root, dirs, files in os.walk(src_dir):
            # dir[:] is required because of it's not a simple slice, but special
            # object, which is used to control recursion in os.walk()
            dirs[:] = [dir_name for dir_name in dirs
                if dir_name not in ['.git', '.hg', '.svn']
            ]

            # get the first proper go file
            for file_name in files:
                if file_name.endswith('_test.go'):
                    continue

                if file_name.endswith('.go'):
                    gofile = file_name

            # if no go files found and parent directory already has a package,
            # skip all hierarchy
            if not gofile:
                if last_package_path and root.startswith(last_package_path):
                    dirs[:] = []
                continue

            full_file_name = os.path.join(root, gofile)
            package_name = get_package_name_from_file(full_file_name)

            # +1 stands for /
            import_path = root[len(src_dir)+1:]

            # fix for standard libraries
            if lib_path == GOROOT and import_path[:4] == "pkg/":
                import_path = import_path[4:]

            if package_name in _imports_cache:
                if len(import_path) < len(_imports_cache[package_name]):
                    _imports_cache[package_name] = import_path
            else:
                _imports_cache[package_name] = import_path

            gofile = None

            # remember top-level package directory
            if not (last_package_path and root.startswith(last_package_path)):
                last_package_path = root

    return _imports_cache

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
            if func:
                if line == current_line:
                    return True
            else:
                return False
        else:
            if func:
                return True

        if line == 0:
            return False

        line = line - 1


const_re = re.compile('^const ')
type_re = re.compile('^type ')
var_re = re.compile('^var ')
func_re = re.compile('^func ')


def move_cursor(line, column):
    vim.command("normal " + str(line) + "gg")
    vim.command("normal " + str(column) + "|")


def goto_re(regexp):
    buffer = vim.current.buffer

    line_number = 0
    for line in buffer:
        line_number += 1
        if regexp.match(line):
            move_cursor(line_number, 0)
            return True

    return None


def goto_re_first_befor_cursor(regexp):
    line_number, column_number = vim.current.window.cursor
    buffer = vim.current.buffer

    while True:
        line = buffer[line_number - 1]
        if regexp.match(line.strip()):
           move_cursor(line_number, 0)

        line_number -= 1
        if line_number == 1:
            return None

    return None


def goto_const():
    return goto_re(const_re) or goto_re(func_re)


def goto_type():
    return goto_re(type_re) or goto_re(func_re)


def goto_var():
    return goto_re(var_re) or goto_re(func_re)


def goto_prev_var():
    return goto_re_first_befor_cursor(var_re)


def is_before_first_func(buffer, line):
    line_iter = 0
    while line_iter <= line:
        if buffer[line_iter][:5] == 'func ':
            return False

        line_iter += 1

    return True


def get_gocode_complete(full = True):
    info = gocode_get_info()
    if not info:
        return ""

    line_number, _ = vim.current.window.cursor
    function_name = vim.current.buffer[line_number - 1].strip()

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
            snippet_return_parts.append('${' + str(placeholder) + ':' + arg + '}')
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
    line, column = vim.current.window.cursor
    vim.current.window.cursor = (line, column - 1)
    info = vim.eval('go#complete#GetInfo()')
    vim.current.window.cursor = (line, column)
    return info
