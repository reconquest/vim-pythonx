# coding=utf8

import vim

import px.cursor


class Highlighter(object):
    def __init__(self):
        self._active_highlights = []

    def clear(self):
        if not self._active_highlights:
            return

        (_, _, current_match_id) = self._active_highlights[-1]
        kept = []
        for active_highlight in self._active_highlights:
            (old_match, old_cursor, match_id) = active_highlight
            if px.cursor.get() == old_cursor and match_id == current_match_id:
                kept.append(active_highlight)
            else:
                try:
                    vim.eval('matchdelete({})'.format(match_id))
                except:
                    pass

        self._active_highlights = kept

    def highlight(self, line_number, column_start, length, group='IncSearch'):
        match_id = vim.eval('matchadd("{0}", \'\%{2}l\%{3}c.{1}\')'.format(
            group,
            '\\{'+str(length)+'\\}',
            *px.cursor.to_vim_lang((line_number, column_start))
        ))

        self._active_highlights.append(
            ((line_number, column_start), px.cursor.get(), match_id)
        )

    def get_active(self):
        return self._active_highlights
