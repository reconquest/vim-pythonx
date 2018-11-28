# coding=utf8

import os
import re
import glob

import px.langs.go
import vim


def guess_package_name_from_file_name():
    path = vim.eval('expand("%:p")')
    dirname = os.path.dirname(os.path.abspath(path))
    if os.path.exists(dirname+"/main.go"):
        return 'main'

    basename = os.path.basename(dirname)

    if re.match(r'^\w+$', basename):
        return basename
    else:
        gofiles = glob.glob(os.path.join(dirname, "*.go"))

        if gofiles:
            for gofile in gofiles:
                package_name = get_package_name_from_file(gofile)

                if package_name:
                    return package_name

        return 'main'


def path_to_import_name(path):
    gopath = px.langs.goGOROOT + ":" + px.langs.go.GOPATH

    for lib_path in gopath.split(':'):
        gofiles = glob.glob(os.path.join(lib_path, "src", path, "*.go"))

        if not gofiles:
            continue

        for gofile in gofiles:
            package_name = get_package_name_from_file(gofile)

            if package_name:
                return package_name


def get_package_name_from_file(path):
    with open(path) as gofile:
        for line in gofile:
            if line.endswith('_test\n'):
                continue
            if line.startswith('package '):
                return line.split(' ')[1].strip()
