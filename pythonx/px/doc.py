# coding=utf8

import re

def get_toc(buffer):
    toc = []
    toc_started = False

    for line_number, line in enumerate(buffer):
        if not line.strip():
            continue

        parsed_item = parse_toc_item(line)

        if not parsed_item:
            if toc:
                break
            else:
                continue

        parsed_item['line'] = line_number

        toc.append(parsed_item)

    return toc



def parse_toc_item(toc_item):
    toc_re = r'((\s*)((\d+\.)*\d+\.?)\s*(.+)\s*)[|*]([^|*]+)[|*]'
    matches = re.match(toc_re, toc_item)

    if matches:
        return {
            'indent': matches.group(2),
            'number': matches.group(3).rstrip('.'),
            'level': matches.group(3).rstrip('.').count('.'),
            'caption': matches.group(5).strip(),
            'justification': len(matches.group(1)),
            'key': matches.group(6)
        }
    else:
        return None


def create_toc_item(number, caption, key, justification=78, indent=''):
    if '.' not in number:
        number += '.'

    left_side = indent + number + ' ' + caption
    fill = ' ' * (justification-len(left_side))
    return left_side + fill + '|{}|'.format(key)


def get_toc_indent(toc):
    for toc_item in toc:
        indent = toc_item['indent']
        if toc_item['indent'] != '':
            return indent[:len(indent)/toc_item['level']]
    else:
        return ''


def insert_toc_item(toc_item, buffer):
    toc = get_toc(buffer)
    toc_indent = get_toc_indent(toc)
    parsed_item = parse_toc_item(toc_item)

    target_line = None
    for toc_item in toc:
        if parsed_item['number'] > toc_item['number']:
            target_line = toc_item['line']
            formatted_item = create_toc_item(
                parsed_item['number'],
                parsed_item['caption'],
                parsed_item['key'],
                justification=toc_item['justification'],
                indent=toc_indent * parsed_item['level']
            )

    if not target_line:
        return False

    buffer[target_line+1:target_line+1] = [formatted_item]

def get_section_level(section):
	return section.rstrip('.').count('.')
