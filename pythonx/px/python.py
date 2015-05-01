# coding=utf8

import re
import all

function_re = re.compile('^def ')
method_re = re.compile('^\s+def ')
class_re = re.compile('^class ')

def ensure_newlines(buffer):
    line_number = 0
    for line in buffer:
        line_number += 1
        if function_re.match(line):
            all.ensure_newlines(buffer, (line_number, 0), 2)
            continue
        if method_re.match(line):
            all.ensure_newlines(buffer, (line_number, 0), 1)
            continue
        if class_re.match(line):
            all.ensure_newlines(buffer, (line_number, 0), 2)
            continue

