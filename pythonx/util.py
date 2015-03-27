# coding=utf8

import vim

HIGHLIGHTS = []


def clear_highlights():
    global HIGHLIGHTS
    remains = []
    cursor = vim.current.window.cursor
    for (old_cursor, match_id) in HIGHLIGHTS:
        if cursor == old_cursor:
            remains.append((old_cursor, match_id))
        else:
            vim.eval('matchdelete({})'.format(match_id))
    HIGHLIGHTS = remains


def highlight(line_number, column_start, length):
    match_id = vim.eval('matchadd("Conceal", \'\%{}l\%{}c.{}\')'.format(
        line_number,
        column_start,
        '\\{'+str(length)+'\\}'
    ))

    HIGHLIGHTS.append((vim.current.window.cursor, match_id))

    vim.command('augroup cycle_by_var_name')
    vim.command('au!')
    vim.command(
        'au CursorMovedI,CursorMoved * py util.clear_highlights()')
    vim.command('augroup end')


def get_buffer_before_cursor():
    cursor = vim.current.window.cursor
    line_number = cursor[0]
    buffer = vim.current.buffer

    return '\n'.join(buffer[:line_number-1])


def get_syntax_name(line, column):
    return vim.eval(
        'synIDattr(synIDtrans(synID({}, {}, 1)), "name")'.format(
            line, column
        )
    )


def convert_camelcase_to_snakecase(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)

    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def get_cword():
    return vim.eval('expand("<cword>")')

def paste(content):
    vim.command('set paste')
    vim.command('normal i' + content)
    vim.command('set nopaste')

def get_pair_line(buffer, line, column):
	vim.command("normal %")
	pair_line = vim.current.buffer[vim.current.window.cursor[0]-1]
	vim.current.window.cursor = (line, column)
	return pair_line

def get_prev_nonempty_line():
    for line in reversed(get_buffer_before_cursor().split('\n')):
        if line.strip() == "":
            continue
        return line
    return ""
