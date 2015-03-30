# coding=utf8

import vim
import datetime

active_highlights = []

def clear():
    global active_highlights
    if not active_highlights:
        return
    cursor = vim.current.window.cursor
    (_, _, current_match_id) = active_highlights[-1]
    kept = []
    for active_highlight in active_highlights:
        (old_match, old_cursor, match_id) = active_highlight
        if cursor == old_cursor and match_id == current_match_id:
            kept.append(active_highlight)
        else:
            vim.eval('matchdelete({})'.format(match_id))
    active_highlights = kept


def highlight(line_number, column_start, length, group='Conceal'):
    global active_highlights

    match_id = vim.eval('matchadd("{}", \'\%{}l\%{}c.{}\')'.format(
        group,
        line_number,
        column_start,
        '\\{'+str(length)+'\\}'
        ))

    active_highlights.append((
        (line_number, column_start),
        vim.current.window.cursor,
        match_id
    ))

    vim.command('augroup px_highlight_clear')
    vim.command('au!')
    vim.command(
        'au CursorMovedI,CursorMoved * py px.highlight.clear()')
    vim.command('augroup end')


def get():
    return active_highlights
