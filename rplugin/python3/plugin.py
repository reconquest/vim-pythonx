import neovim
import logging
import os
import os.path
import glob
import sys
import shutil

sys.path.append(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

@neovim.plugin
class Main(object):
    def __init__(self, vim=None):
        self.vim = vim

    @neovim.function('PythonxJavaChooseImport', sync=True)
    def choose_import(self, args):
        candidates = args[0]

        path = os.path.dirname(self.vim.current.buffer.name)
        fullpath = path

        java = path.rfind('/java/')
        if java == -1:
            return -1

        path = path[:java+len('/java/')]

        candidates_pkgs = {}
        pkgs_candidates = {}
        for candidate in candidates:
            pkg = get_package(candidate)
            candidates_pkgs[candidate] = pkg
            pkgs_candidates[pkg] = candidate

        votes_class = {}
        votes_package = {}

        # x = ""
        for dirpath, _, files in os.walk(path):
            for name in files:
                if not name.endswith(".java"):
                    continue

                (imports_class, imports_packages) = get_imports(
                    os.path.join(dirpath, name)
                )
                # x += " name: " + name
                # x += " imports_class: " + str(imports_class)
                # x += " imports_packages: " + str(imports_packages)
                for candidate in candidates:
                    if candidate in imports_class:
                        if not candidate in votes_class:
                            votes_class[candidate] = 1
                        else:
                            votes_class[candidate] += 1
                    else:
                        if candidates_pkgs[candidate] in imports_packages:
                            if not candidate in votes_package:
                                votes_package[candidate] = 1
                            else:
                                votes_package[candidate] += 1

        if len(votes_class) > 0:
            votes = votes_class
        else:
            votes = votes_package

        if len(votes) == 0:
            return -1

        def maxVal(kv):
             keys = list(kv.keys())
             values = list(kv.values())
             return keys[values.index(max(values))]

        biggest = maxVal(votes)
        for i in range(len(candidates)):
            if biggest == candidates[i]:
                return i

        return -1


def get_imports(filepath):
    classes = []
    packages = []
    with open(filepath) as file:
        for line in file:
            if line.startswith('//'):
                continue

            if line.startswith('import '):
                path = line.rstrip()[7:-1]
                classes.append(path)

                pkg = get_package(path)
                if not pkg in packages:
                    packages.append(pkg)

                continue

            if line.startswith('package'):
                continue

            if line.strip() == "":
                continue

            break
    return (classes, packages)


def get_package(path):
    chunks = path.split('.')
    return '.'.join(chunks[:-1])
