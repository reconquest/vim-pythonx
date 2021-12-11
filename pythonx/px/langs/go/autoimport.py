# coding=utf8

import os
import shutil
import os
import re
import vim
import collections
import subprocess
import json
# import logging

import px
import px.util
import px.buffer
import px.syntax
import px.cursor
import px.langs.go
import px.langs.go.packages

DEFAULT_EXCLUDE = [
    '.git',
    '.hg',
    '.svn',
    'examples',
    'example',
    'testdata',
    'tests',
    'test',
    'vendor',
]

class Autoimporter(object):
    def __init__(
        self,
        cache_path=os.getenv('HOME')+'/.cache/vim-pythonx/go/autoimport',
        exclude=DEFAULT_EXCLUDE
    ):
        self._cache_path = cache_path
        if not os.path.exists(self._cache_path):
            os.makedirs(self._cache_path)
        self._cached_packages = None
        self._cached_imports = None

        self._exclude = exclude

        self.load_cache_packages()
        self.load_cache_imports()

        self.print_indexing = False

    def get_cache_path_packages(self):
        return self._cache_path + "/packages"

    def get_cache_path_imports(self):
        return self._cache_path + "/imports"

    def get_cache_path_files(self):
        return self._cache_path + "/files"

    def load_cache_packages(self):
        path = self.get_cache_path_packages()
        if not os.path.exists(path):
            return None
        with open(path) as infile:
            self._cached_packages = json.load(infile)

    def load_cache_imports(self):
        path = self.get_cache_path_imports()
        if not os.path.exists(path):
            return None
        with open(path) as infile:
            self._cached_imports = json.load(infile)

    def save_cache_packages(self):
        with open(self.get_cache_path_packages(), 'w') as outfile:
            json.dump(self._cached_packages, outfile)

    def save_cache_imports(self):
        with open(self.get_cache_path_imports(), 'w') as outfile:
            json.dump(self._cached_imports, outfile)

    def reset(self):
        self._cached_packages = None
        self._cached_imports = None

    def drop_cache(self):
        print("vim-pythonx: dropping cache")
        shutil.rmtree(self._cache_path)
        os.makedirs(self._cache_path)

    def autoimport_at_cursor(self):
        cursor = px.cursor.get()

        if px.syntax.is_number(cursor):
            return

        if px.syntax.is_string(cursor):
            return

        if px.syntax.is_comment(cursor):
            return

        buffer = px.buffer.get()
        (line, column) = px.cursor.get()

        identifier_data = px.identifiers.get_under_cursor(
            buffer, (line, column),
        )

        if not identifier_data:
            return

        identifier, _ = identifier_data

        if not identifier:
            return

        if identifier.count('.') >= 1:
            return

        if re.match(r'^\d+$', identifier):
            return

        info = ""
        try:
            info = px.langs.go.gocode_get_info(identifier)
        except Exception:
            raise

        if info != "" and re.match("^(var|type|package) \w+", info):
            return

        possible_package = identifier.split('.')[0]

        import_path = self.get_import_path_for_identifier(possible_package)
        if not import_path:
            return

        vim.command("call px#go#import('{}')".format(import_path))

    def get_go_mod(self, dir):
        process = subprocess.Popen(["go", "list", "-m", "-json"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='UTF-8')
        output, _ = process.communicate()
        if process.returncode != 0:
            return (None, None)
        mod = json.loads(output)
        return (mod['Path'], mod['Dir'])

    def get_import_path_for_identifier(self, identifier, reset=False):
        cwd = os.getcwd()

        (go_mod, go_mod_dir) = self.get_go_mod(cwd)
        if go_mod_dir:
            cwd = go_mod_dir

        subpackages = self.get_subpackages_from_dir(cwd)
        if identifier in subpackages:
            return subpackages[identifier]

        all_imports = self.get_all_imports_cached()

        imports = self.get_project_imports()
        contenders = {}
        for import_path in imports:
            if go_mod is not None:
                import_path = px.util.remove_prefix(
                    import_path,
                    go_mod + '/vendor/'
                )

                if import_path.startswith(
                    go_mod + '/internal/'
                ):
                    continue
            else:
                if '/internal/' in import_path:
                    continue

            if not reset:
                if not import_path in all_imports and not import_path.find('/vendor'):
                    print(
                        "vim-pythonx: unknown package is "+
                        "imported in the program: " + import_path)

                    self.reset()
                    self.drop_cache()

                    print("vim-pythonx: re-caching resources")

                    return self.get_import_path_for_identifier(
                        identifier,
                        reset=True
                    )

            if import_path in all_imports:
                package = all_imports[import_path]
                if package == identifier:
                    if import_path in contenders:
                        contenders[import_path] += 1
                    else:
                        contenders[import_path] = 1

        if len(contenders) > 0:
            (contender, _) = sorted(
                contenders.items(),
                key=lambda item: item[1],
                reverse=True
            )[0]
            return contender

        packages = self.get_all_packages()
        if identifier not in packages:
            return None

        return packages[identifier]

    def _read_file_package_cache(self):
        if not os.path.exists(self.get_cache_path_files()):
            return {}

        file_package = {}

        with open(self.get_cache_path_files(), 'r+') as cache:
            for line in cache:
                file, package = line.rstrip('\n').split(':')
                file_package[file] = package

        return file_package

    def _write_file_package_cache(self, file_package):
        with open(self.get_cache_path_files(), 'w') as cache:
            lines = []
            for (file, package) in file_package.items():
                lines.append(file + ':' + package)
            cache.write('\n'.join(lines))

    def get_project_imports(self):
        target_dir = "./..."
        # do not run recursive go list for non-GOPATH directories since it can
        # cause too long wait
        # there could be used subprocess/wait with timeout, but it's available
        # only in Python 3
        if not os.getcwd().startswith(os.path.join(px.langs.go.GOPATH, "src")):
            target_dir = "./"

        process = subprocess.Popen(
            [
                "go",
                "list",
                "-f",
                "{{ range $path := .Imports}}{{$path}}{{\"\\n\"}}{{end}}",
                target_dir,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='UTF-8'
        )
        output, _ = process.communicate()
        lines = output.split("\n")

        # drop last empty line
        lines = lines[:-1]

        return lines

    def get_all_imports_cached(self):
        if self._cached_imports:
            return self._cached_imports

        self.get_all_packages()

        return self._cached_imports

    def get_all_packages(self):
        if self._cached_packages:
            return self._cached_packages

        packages = {}
        imports = {}

        imports_data = collections.OrderedDict(
            sorted(self.get_imports_data().items(), key=lambda x: len(x[0]))
        )

        file_package_cache = self._read_file_package_cache()
        new_file_package_cache = {}

        for (import_path, file) in imports_data.items():
            if file in file_package_cache:
                package = file_package_cache[file]
            else:
                package = px.langs.go.packages.get_package_name_from_file(file)

            if not package:
                continue

            if package not in packages:
                packages[package] = import_path

            if import_path not in imports:
                imports[import_path] = package

            new_file_package_cache[file] = package

        self._write_file_package_cache(new_file_package_cache)

        self._cached_packages = packages
        self._cached_imports = imports

        self.save_cache_packages()
        self.save_cache_imports()

        if self.print_indexing:
            print(
                "vim-pythonx: indexed "+str(len(self._cached_packages))+" packages"
            )

        return packages


    def get_subpackages_from_dir(self, directory):
        packages = {}
        imports = {}

        # support local imports only in GOPATH for now
        root_dir = os.path.join(px.langs.go.GOPATH, "src")
        if not directory.startswith(root_dir):
            return packages

        imports_data = collections.OrderedDict(
            sorted(
                self._get_import_path_from_dir(directory, root_dir).items(),
                key=lambda x: len(x[0])
            )
        )

        for (import_path, file) in imports_data.items():
            package = px.langs.go.packages.get_package_name_from_file(file)

            if not package:
                continue

            if package not in packages:
                packages[package] = import_path

            if import_path not in imports:
                imports[import_path] = package

        return packages

    def get_imports_data(self):
        imports = {}

        for root_dir in [px.langs.go.GOPATH, px.langs.go.GOROOT]:
            imports.update(self._get_import_path_from_dir(
                os.path.join(root_dir, "src")
            ))

        return imports

    def _get_import_path_from_dir(self, root_src_dir, root_dir=None):
        imports = {}

        if root_dir is None:
            root_dir = root_src_dir

        last_package_dir = None
        last_package_go_mod = None
        last_package_dir_depth = 0

        max_depth_blind = 5

        for package_dir, dirs, files in os.walk(root_src_dir, followlinks=True):
            # skip vgo vendored
            if package_dir.startswith(root_src_dir + "/v/"):
                dirs[:] = []
                continue

            # dir[:] is required because of it's not a simple slice, but
            # special object, which is used to control recursion in
            # os.walk()
            dirs[:] = self._filter_exclude(dirs)

            go_mod = self._find_go_mod_package(package_dir, files)
            if not last_package_go_mod or not (last_package_dir and package_dir.startswith(last_package_dir)):
                last_package_go_mod = go_mod

            go_file = self._find_first_go_package_file(package_dir, files)

            # if no go files found and parent directory already has
            # a package, prune directory
            if not go_file:
                if last_package_dir:
                    depth = package_dir.count("/") - last_package_dir_depth
                    if depth > max_depth_blind:
                        if package_dir.startswith(last_package_dir):
                            dirs[:] = []
                        else:
                            last_package_dir = None
                            last_package_go_mod = None
                            last_package_dir_depth = 0
                continue


            if last_package_go_mod:
                package_import = last_package_go_mod + package_dir[len(last_package_dir):]
            else:
                if root_dir != package_dir:
                    # +1 stands for /
                    package_import = package_dir[len(root_dir)+1:]
                else:
                    package_import = os.path.basename(package_dir)

                # fix for standard libraries
                if root_dir.startswith(px.langs.go.GOROOT):
                    if package_import[:4] == "pkg/":
                        package_import = package_import[4:]

            imports[package_import] = package_dir + "/" + go_file

            # remember top-level package directory
            if not (last_package_dir and
                    package_dir.startswith(last_package_dir)):
                last_package_dir = package_dir
                last_package_dir_depth = last_package_dir.count("/")

        return imports

    def _filter_exclude(self, dirs):
        filtered = []

        for dir_name in dirs:
            if not dir_name.startswith('.') and not dir_name.startswith('_'):
                if dir_name not in self._exclude:
                    filtered.append(dir_name)

        return filtered

    def _find_first_go_package_file(self, dir, files):
        for file in files:
            if file.endswith('_test.go'):
                continue

            if file.endswith('.go'):
                package = px.langs.go.packages.get_package_name_from_file(
                    dir + "/" + file
                )
                if package != "main":
                    return file

    def _find_go_mod_package(self, dir, files):
        for file in files:
            if file != 'go.mod':
                continue

            with open(dir + "/" + file) as gomod:
                for line in gomod:
                    if line.startswith('module '):
                        return line.split(' ')[1].strip()
        return None
