# # coding=utf8

# import vim
# import re
# import os
# import subprocess
# import glob

# import px.util
# import px.highlight

# import px.all

# IDENTIFIERS_RE = r'(protected|public|private|var)?\s?(\$(\w+(->)?)+)(?!\w*\()'

# def _prepend_this_to_var_name(match):
    # if match.group(1):
        # return ('$this->' + match.group(2)[1:], match.start(2))
    # else:
        # return (match.group(2), match.start(2))


# def get_class_name_with_underscored_namespaces(path=""):
    # """ Returns a class name with expanded namespaces from path variable """
    # if not path:
        # path = vim.eval('expand("%p")')

    # path = path.replace('.php', '')
    # class_name = re.sub(r'(?!^)\/([a-zA-Z])', lambda m: '_' + m.group(1).upper(), path)
    # return class_name

# def get_possible_identifiers(buffer, cursor):
    # all.get_possible_identifiers(
        # buffer, cursor,
        # IDENTIFIERS_RE,
        # _prepend_this_to_var_name,
    # )

    # return identifiers

# def get_identifier_from_string(string, with_dollar=True):
    # (identifier, _) = util.get_identifier_from_string(
            # string,
            # '(\$[\w_\->]+)',
            # extract=lambda m: (m.group(1), m.start(1))
    # )

    # if not identifier:
        # return None

    # if with_dollar == False and identifier[0] == '$':
        # return identifier[1:]
    # else:
        # return identifier

# def highlight(cursor, identifier):
    # under_cursor = vim.current.buffer[cursor[0]-1][cursor[1]-1:]
    # if not under_cursor.startswith(identifier):
        # identifier = identifier.replace('$this->', '$')

    # return all.default_highlight(cursor, identifier)


# def cycle_by_var_name(
    # identifiers=[],
    # pattern=IDENTIFIERS_RE,
    # extract=_prepend_this_to_var_name,
    # should_skip=None,
    # highlighting=highlight,
# ):
    # if not should_skip:
        # def should_skip(_, (line, column)):
            # return all.get_syntax_name((line, column + 1)) != 'Identifier'
    # return all.cycle_by_var_name(
        # identifiers, pattern, extract, should_skip, highlighting
    # )


# def get_identifier_under_cursor(buffer, cursor, with_dollar=True):
    # (line_number, column_number) = cursor
    # line = buffer[line_number-1][:column_number]

    # (identifier, _) = get_identifier_from_string(line, with_dollar)
    # if identifier:
        # return (identifier, (line_number, column_number - len(identifier) + 1))
    # else:
        # return None

# def smart_convert_to_camelcase(identifier):
    # """
    # Smart converting variables to camelCase names.
    # """
    # if identifier[0] == '_':
        # identifier = identifier[1:]

    # identifier = identifier[:1].capitalize() + identifier[1:]

    # return identifier

# def get_camelcase_identifier_from_string(string, with_dollar=True):
    # """
    # Returns camelCase identifier from string, for example:
    # `protected $_storage;`
    # returns just `Storage`
    # """

    # return smart_convert_to_camelcase(get_identifier_from_string(string, with_dollar))

# def get_phpdoc_variables_before_cursor():
    # """
    # Returns key-value data from phpdoc before current cursor position.
    # Sometimes value may be array
    # """
    # line_number, _ = vim.current.window.cursor
    # buffer = vim.current.window.buffer

    # variables = {}
    # i = 0
    # while i < 10:
        # i = i + 1
        # line = buffer[line_number-i]
        # matches = re.search('\* \@([\w]+) (.*)', line)
        # if not matches:
            # continue

        # name = matches.group(1)
        # value = matches.group(2)

        # if name in variables:
            # if isinstance(variables[name], list):
                # variables[name].insert(0, value)
            # else:
                # variables[name] = [variables[name], value]
        # else:
            # variables[name] = value

    # return variables

# def get_last_var_for_snippet():
    # return all.get_last_var_for_snippet(IDENTIFIERS_RE)
