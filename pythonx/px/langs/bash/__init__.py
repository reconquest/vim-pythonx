import px
import px.buffer
import px.cursor

def split_line():
    buffer = px.buffer.get()
    cursor = px.cursor.get()
    line_number, column = cursor
    line = buffer[line_number]

    result = _split_line(line.split("\n"))

    buffer[line_number:line_number+1] = result


def _split_line(lines):
    result = []
    changed = False
    for line in lines:
        if len(line) > 80:
            chunks = line.split(' -', 1)
            result.append(chunks[0] + " \\")
            result.append("\t-"+chunks[1])
            changed = True
        else:
            result.append(line)
    if not changed:
        return result
    return _split_line(result)


def get_indent(line):
    level = 0
    tab = "\t"
    for symbol in line:
        if symbol == "\t" or symbol == " ":
            tab = symbol
            level += 1
        else:
            break

    return (tab, level)
