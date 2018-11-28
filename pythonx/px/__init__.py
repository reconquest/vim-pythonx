# coding: utf-8

import pkgutil
import importlib
import os

imported = {}
def libs(package="px"):
    if isinstance(package, str):
        package = importlib.import_module(package)

    for loader, name, is_pkg in pkgutil.walk_packages(package.__path__):
        full_name = package.__name__ + '.' + name
        if full_name in imported:
            continue

        imported[full_name] = name
        if is_pkg:
            imported.update(libs(full_name))
    return imported

# import logging

# logging.basicConfig(
#     filename='/tmp/vim-pythonx.log',
#     format='%(filename)s:%(lineno)s %(funcName)s: %(message)s',
#     level=logging.DEBUG
# )
