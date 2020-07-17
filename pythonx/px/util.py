# coding=utf8

import re
import vim

def convert_camelcase_to_snakecase(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)

    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def convert_camelcase_to_kebabcase(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', name)

    return re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1).lower()


def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    else:
        return text
