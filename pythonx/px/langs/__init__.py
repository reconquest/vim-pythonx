import px
import px.cursor
import px.buffer

def goto_re(regexp):
    match = find_re(regexp)
    if match:
        px.cursor.set(match)
        return True
    return False

def find_re(regexp):
    line_number = 0
    for line in px.buffer.get():
        line_number += 1

        if regexp.match(line):
            return (line_number, 0)

    return None

def goto_re_first_before_cursor(regexp):
    match = find_re_first_before_cursor(regexp)
    if match:
        px.cursor.set(match)
        return True
    return False

def find_re_first_before_cursor(regexp):
    line_number, column_number = px.cursor.get()

    buffer = px.buffer.get()
    while True:
        line = buffer[line_number - 1]
        if regexp.match(line):
            return (line_number, 0)

        line_number -= 1
        if line_number == 1:
            return None

    return None

def find_re_first_after_cursor(regexp, callback=None):
    line_number, column_number = px.cursor.get()

    buffer = px.buffer.get()
    while True:
        line = buffer[line_number - 1]
        matches = regexp.match(line)
        if matches:
            if not callback or callback(matches):
                return (line_number, 0)

        line_number += 1
        if line_number > len(buffer) - 1:
            return None

    return None
