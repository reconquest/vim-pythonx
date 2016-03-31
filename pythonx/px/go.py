# coding=utf8

import vim
import re
import os
import subprocess
import glob
import collections

import px.util
import px.all

GOROOT = subprocess.check_output(['go', 'env', 'GOROOT']).strip()
GOPATH = subprocess.check_output(['go', 'env', 'GOPATH']).strip()

CACHE_IMPORT_TO_PACKAGE = os.getenv('HOME') + '/.cache/vim-pythonx.imports'

GO_SYNTAX_ITEMS = [
    'String',
    'Keyword',
    'Repeat',
    'Conditional',
    'Number',
    'Statement',
    'Type',
]

_cache_all_packages = {}

def extract_prev_method_binding_for_cursor():
    search_space = px.all.get_buffer_before_cursor()

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
    search_space = px.all.get_buffer_before_cursor()
    matches = re.findall(r'(\w+)\[', search_space)

    if matches:
        return matches[-1]

    return ""


def split_parenthesis():
    first_paren = vim.eval('searchpos("(", "bc")')
    vim.command('exec "normal a\<CR>"')
    vim.command('call search("(", "bc")')
    vim.current.window.cursor = (int(first_paren[0]), int(first_paren[1]))
    vim.command('normal %')
    vim.command('exec "normal ha,\<CR>"')


def is_if_bracket(buffer, line, column):
    return px.all.get_pair_line(buffer, line, column).strip().startswith("if")


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
        px.all.get_pair_line(buffer, line, column))
    is_method_def = re.match("^func \(\w+ \w+\) ",
        px.all.get_pair_line(buffer, line, column))
    return is_struct_def or is_method_def


def autoimport():
    if px.all.is_syntax_string(vim.current.window.cursor):
        return

    info = ""
    try:
        info = vim.eval('go#complete#GetInfo()')
    except Exception:
        pass

    if info != "" and re.match("^var \w+", info):
        return

    identifier_data = px.util.get_identifier_under_cursor(
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
    packages = get_all_packages()
    if identifier not in packages:
        return None
    return packages[identifier]

def _read_file_package_cache():
    if not os.path.exists(CACHE_IMPORT_TO_PACKAGE):
        return {}

    file_package = {}

    with open(CACHE_IMPORT_TO_PACKAGE, 'r+') as cache:
        for line in cache:
            file, package = line.rstrip('\n').split(':')
            file_package[file] = package

    return file_package

def _write_file_package_cache(file_package):
    with open(CACHE_IMPORT_TO_PACKAGE, 'w') as cache:
        lines = []
        for (file, package) in file_package.items():
            lines.append(file + ':' + package)
        cache.write('\n'.join(lines))

def get_all_packages():
    global _cache_all_packages

    if _cache_all_packages:
        return _cache_all_packages

    packages = {}

    imports_data = collections.OrderedDict(
        sorted(get_imports_data().items(), key=lambda x: len(x[0]))
    )

    file_package_cache = _read_file_package_cache()
    new_file_package_cache = {}

    for (import_path, file) in imports_data.items():
        if file in file_package_cache:
            package = file_package_cache[file]
        else:
            package = get_package_name_from_file(file)

        if not package in packages:
            packages[package] = import_path

        new_file_package_cache[file] = package

    _write_file_package_cache(new_file_package_cache)

    _cache_all_packages = packages

    return packages

def get_imports_data():
    exclude = [
        '.git',
        '.hg',
        '.svn',
        'examples',
        'example',
        'testdata',
        'tests',
        'test',
        'vendor',
    ]

    imports = {}

    for root_dir in [ GOPATH]:
        root_src_dir = os.path.join(root_dir, "src")
        last_package_dir = None
        for package_dir, dirs, files in os.walk(root_src_dir):
            # dir[:] is required because of it's not a simple slice, but special
            # object, which is used to control recursion in os.walk()
            dirs[:] = [dir_name for dir_name in dirs
                if dir_name not in exclude
            ]

            go_file = False
            for file in files:
                if file.endswith('_test.go'):
                    continue

                if file.endswith('.go'):
                    go_file = file
                    break

            # if no go files found and parent directory already has a package,
            # prune directory
            if not go_file:
                if last_package_dir:
                    if package_dir.startswith(last_package_dir):
                        dirs[:] = []
                    else:
                        last_package_dir = None
                continue

            # +1 stands for /
            package_import = package_dir[len(root_src_dir)+1:]

            # fix for standard libraries
            if root_dir == GOROOT and package_import[:4] == "pkg/":
                package_import = package_import[4:]

            imports[package_import] = package_dir + "/" + go_file

            # remember top-level package directory
            if not (last_package_dir and \
                    package_dir.startswith(last_package_dir)):
                last_package_dir = package_dir

    return imports

def get_package_name_from_file(path):
    with open(path) as gofile:
        for line in gofile:
            if line.startswith('package '):
                return line.split(' ')[1].strip()

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
