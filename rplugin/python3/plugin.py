import neovim
import logging
import os
import os.path
import glob
import sys
import shutil
import json

sys.path.append(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

@neovim.plugin
class Main(object):
    def __init__(self, vim=None):
        self.vim = vim
        self._last_diagnostic = []
        self.setup_log()

    def setup_log(self):
        handler = logging.FileHandler('/tmp/rplugin.log')
        handler.setLevel(logging.DEBUG)

        self.log = logging.getLogger('rplugin')
        self.log.setLevel(logging.DEBUG)
        self.log.addHandler(handler)

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

        for dirpath, _, files in os.walk(path):
            for name in files:
                if not name.endswith(".java"):
                    continue

                (imports_class, imports_packages) = get_imports(
                    os.path.join(dirpath, name)
                )
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

    def _get_coc_diagnostic(self):
        cwd = os.getcwd()

        def _map(item):
            filename = item['file']
            if filename.startswith(cwd):
                filename = filename[len(cwd) + 1:]

            item['file'] = filename

            return item

        def _filter(item):
            if item['severity'] != 'Error' and item['severity'] != 'Warning':
                return False

            if item['file'].endswith('Compat.java') or item['file'].endswith('go.mod'):
                return False

            return True

        def _sort(item):
            if "Syntax error" in item['message']:
                return 0
            return 1

        raw = self.vim.eval("CocAction('diagnosticList')")
        if not raw:
            return []

        result = list(
            sorted(filter(_filter, map(_map, raw)), key=_sort)
        )

        return result

    @neovim.function('PythonxCocDiagnosticFirst', sync=True)
    def coc_diagnostic_first(self, args):
        diagnostic = self._get_coc_diagnostic()
        if len(diagnostic) == 0:
            return

        self._jump_diagnostic(diagnostic[0])

    @neovim.function('PythonxCocDiagnosticNext', sync=True)
    def coc_diagnostic_next(self, args):
        diagnostic = self._get_coc_diagnostic()
        if len(diagnostic) == 0:
            return

        if self._last_diagnostic != diagnostic:
            self._last_diagnostic = diagnostic
            self._diagnostic_point = 0
        else:
            self._diagnostic_point += 1
            if self._diagnostic_point >= len(diagnostic):
                self._diagnostic_point = 0

        self._jump_diagnostic(diagnostic[self._diagnostic_point])

    def _jump_diagnostic(self, item):
        cwd = os.getcwd()

        name = self.vim.current.buffer.name

        relname = name
        if relname.startswith(cwd):
            relname = relname[len(cwd)+1:]

        if name != item['file'] and relname != item['file']:
            self.vim.command('edit ' + item['file'])

        line = item['lnum']
        char = item['col']

        self.vim.eval('coc#util#jumpTo(' + str(line-1) + ', ' + str(char) + ')')

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
