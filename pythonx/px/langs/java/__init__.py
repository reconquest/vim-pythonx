import px
import px.langs
import px.buffer
import px.cursor
import re
import os.path
import operator

from px.langs import *

const_re = re.compile(r'^\s+(public )?(static )?(final )?([\w\d_]+)\s+([\w\d_]+)\s+=')
class_re = re.compile(r'^(public |private )?(final )?(class|interface) ')
private_decls_re = re.compile(r'^\s+private ([\w\d_]+) ([\w\d_]+);')
constructor_setters_re = re.compile(r'^\s+this.([\w\d_]+) = ([\w\d_]+);')
constructor_re = re.compile(r'^\s+public ([\w\d_]+)\(')

def get_var_name_by_class_name(name):
    if name == "ActiveObjects":
        return "ao"

    if '.' in name:
        chunks = name.split('.')
        name = chunks[-1]

    if len(name) > 0:
        name = name[0].lower() + name[1:]
    return name


def goto_const():
    went = goto_re_first_before_cursor(const_re)
    if not went:
        return goto_re(class_re)
    return True


def goto_private_decls():
    went = goto_re_first_before_cursor(private_decls_re)
    if not went:
        return goto_const()
    return True


def goto_constructor_setters():
    match = find_re_first_after_cursor(constructor_setters_re, _is_constructor_setter)
    if match:
        px.cursor.set((match[0]-1, match[1]))
        return True
    cursor = px.cursor.get()
    px.cursor.set((cursor[0]+1, cursor[1]))


def _is_constructor_setter(match):
    return match.group(1) == match.group(2)


def ensure_import(buffer, importpath):
    i = 0
    last_import = 0
    while True:
        i += 1
        if i > len(buffer)-1:
            break

        line = buffer[i]

        if line.startswith('//'):
            continue

        if line.startswith('import '):
            item = line[7:-1]
            last_import = i

            if item == importpath:
                return True

            continue

        if line.startswith('package '):
            continue

        if line.strip() == "":
            continue

        break

    px.buffer.insert_lines_before(
        buffer,
        (last_import+1, 0),
        ["import "+importpath + ";"]
    )
