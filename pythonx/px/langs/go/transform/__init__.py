import vim
import px
import px.buffer
import px.cursor
import logging

class Selection(object):
    def _get_start_pos(self):
        return vim.current.buffer.mark('<')

    def _get_end_pos(self):
        return vim.current.buffer.mark('>')

    def __init__(self):
        self.buffer = px.buffer.get()
        self.cursor = px.cursor.get()
        self.line_number, self.column = self.cursor

        self.start_pos = self._get_start_pos()
        self.end_pos = self._get_end_pos()

        self.start_line, self.start_column = self.start_pos
        self.end_line, self.end_column = self.end_pos

        self.line = self.buffer[self.line_number]
        self.selection = self.line[self.start_column:self.end_column+1]


    def get(self):
        return self.selection

    def set(self, payload):
        self.buffer[self.line_number] = \
            self.line[:self.start_column] + \
                payload + \
                self.line[self.end_column+1:]


def _set_clipboard(str):
    enclose = lambda str: "'"+str.replace("'", "''")+"'"
    vim.eval("setreg('*', {0})".format(enclose(str)))


def _get_input(str):
    return vim.eval("input('{0}')".format(str))


def to_variable():
    selection = Selection()

    try:
        var_name = _get_input('Export to Variable: ')
    except:
        return

    selection.set(var_name)

    clipboard = var_name + ' := ' + selection.get()
    _set_clipboard(clipboard)
