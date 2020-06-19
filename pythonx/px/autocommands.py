# coding=utf8

import vim

def disable_identifier_completion_auto_reset():
    vim.command('augroup px_completion_reset')
    vim.command('au!')
    vim.command('augroup end')


def enable_identifier_completion_auto_reset():
    vim.command('augroup px_completion_reset')
    vim.command('au!')
    vim.command(
        'au CursorMovedI,CursorMoved * '
        'py3 px.common.reset_identifier_completion()')
    vim.command('augroup end')


def enable_highlight_auto_clear():
    vim.command('augroup px_highlight_clear')
    vim.command('au!')
    vim.command(
        'au CursorMovedI,CursorMoved * py3 px.common.clear_highlight()')
    vim.command('augroup end')


def disable_higlight_auto_clear():
    vim.command('augroup px_highlight_clear')
    vim.command('au!')
    vim.command('augroup end')


def enable_cursor_moved_callbacks():
    vim.command('augroup px_cursor_callbacks_moved')
    vim.command('au!')
    vim.command(
        'au CursorMovedI,CursorMoved * '
        'py3 px.common.run_cursor_moved_callbacks()')
    vim.command('augroup end')
