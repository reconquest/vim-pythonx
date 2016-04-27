# coding: utf-8

import pkgutil
import importlib

def libs(package="px"):
    if isinstance(package, str):
        package = importlib.import_module(package)

    results = {}
    for loader, name, is_pkg in pkgutil.walk_packages(package.__path__):
        full_name = package.__name__ + '.' + name
        results[full_name] = name
        if is_pkg:
            results.update(libs(full_name))
    return results
