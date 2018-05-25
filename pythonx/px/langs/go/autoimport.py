# coding=utf8

import os
import shutil
import os
import re
import vim
import collections
import subprocess
import json

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
    'internal', # case for Go internals such as internal/pprof/profile
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

        if identifier.count('.') > 1:
            return

        info = ""
        try:
            info = px.langs.go.gocode_get_info()
        except Exception:
            raise

        if info != "" and re.match("^(var|type|package) \w+", info):
            return

        possible_package = identifier.split('.')[0]

        import_path = self.get_import_path_for_identifier(possible_package)
        if not import_path:
            return

        vim.command('GoImport {}'.format(import_path))

    def get_import_path_for_identifier(self, identifier, reset=False):
        all_imports = self.get_all_imports()

        imports = self.list_imports()
        for import_path in imports:
            if not reset:
                if not import_path in all_imports:
                    print("vim-pythonx: unknown package is imported in the program")

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
                    return import_path

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

    def list_imports(self):
        process = subprocess.Popen(
            [
                "go",
                "list",
                "-f",
                "{{ range $path := .Imports}}{{$path}}{{\"\\n\"}}{{end}}"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        output, _ = process.communicate()
        lines = output.split("\n")

        # drop last empty line
        lines = lines[:-1]

        return lines


    def get_all_imports(self):
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

        return packages

    def get_imports_data(self):
        imports = {}

        for root_dir in [px.langs.go.GOPATH, px.langs.go.GOROOT]:
            imports.update(self._get_imports_from_dir(root_dir))

        return imports

    def _get_imports_from_dir(self, root_dir):
        imports = {}

        root_src_dir = os.path.join(root_dir, "src")
        last_package_dir = None
        for package_dir, dirs, files in os.walk(root_src_dir):
            # dir[:] is required because of it's not a simple slice, but
            # special object, which is used to control recursion in
            # os.walk()
            dirs[:] = self._filter_exclude(dirs)

            go_file = self._find_first_go_package_file(package_dir, files)

            # if no go files found and parent directory already has
            # a package, prune directory
            if not go_file:
                if last_package_dir:
                    if package_dir.startswith(last_package_dir):
                        dirs[:] = []
                    else:
                        last_package_dir = None
                continue

            # +1 stands for /
            package_import = package_dir[len(root_src_dir)+1:]

            # fix for standard libraries
            if root_dir == px.langs.go.GOROOT:
                if package_import[:4] == "pkg/":
                    package_import = package_import[4:]

            imports[package_import] = package_dir + "/" + go_file

            # remember top-level package directory
            if not (last_package_dir and
                    package_dir.startswith(last_package_dir)):
                last_package_dir = package_dir

        return imports

    def _filter_exclude(self, dirs):
        filtered = []

        for dir_name in dirs:
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
