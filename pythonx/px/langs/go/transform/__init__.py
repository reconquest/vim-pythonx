import vim
import px
import logging

from structs import *

def start_pos():
    return vim.current.buffer.mark('<')

def end_pos():
    return vim.current.buffer.mark('<')

def selection():
    return vim.current.range
