#!/usr/bin/env python

from multiprocessing import cpu_count
from shlex import split as cmdsplit
import urllib.request
import subprocess
import argparse
import shutil
import sys
import os
import re


JEMALLOC_PREFIX = "je_"

EXTRA_FLAGS = [
    "-fvisibility=hidden", "-fexec-charset=UTF-8"
]

GCC_LTO_FLAGS = ["-flto", "-fno-fat-lto-objects"]

CLANG_LTO_FLAGS = ["-flto=thin"]

SOURCE_DIR = os.path.realpath(os.path.dirname(os.path.realpath(__file__)))

BUILD_DIR = os.path.join(SOURCE_DIR, "build")

INSTALL_DIR = os.path.join(SOURCE_DIR, "install")

CONFIG_FLAGS = [
    "--disable-cxx", "--disable-static", "--disable-prof",
    "--with-jemalloc-prefix=%s" % (JEMALLOC_PREFIX),
    "--prefix=%s" % (INSTALL_DIR),
    "--libdir=%s" % (INSTALL_DIR),
    "--includedir=%s" % (INSTALL_DIR)
]

MAKE_COMMAND = "mingw32-make" if os.name == 'nt' else "make"


def do_call(arg):
    print("> " + arg, flush=True)
    args = cmdsplit(arg)
    try:
        subprocess.check_call(args, env=os.environ)
    except subprocess.CalledProcessError as error:
        print(error, flush=True)
        print(error.output, flush=True)
        sys.exit(1)


def get_compiler_info():
    "Figure out which C/C++ compiler we are using and what version."
    compiler_cmd = os.environ["CC"] if "CC" in os.environ else "cc"
    args = [compiler_cmd, "-v"]
    print("> " + " ".join(args), flush=True)
    try:
        version_info = subprocess.check_output(
            args, env=os.environ, stderr=subprocess.STDOUT)
        version_info = version_info.decode("utf-8")
        version_info_match = re.search(
            r"^(\w+) version ([\.\d]+)", version_info, re.MULTILINE)
        if version_info_match is None:
            print(version_info, "Could not parse compiler information!",
                  sep='\n', flush=True)
            return ("Unknown", "Unknown")
        else:
            name = version_info_match.group(1)
            version = version_info_match.group(2)
            return name, version
    except subprocess.CalledProcessError as error:
        print(error, flush=True)
        print(error.output, flush=True)
        sys.exit(1)


def is_clang():
    name = get_compiler_info()[0]
    return name == "clang"


def shell_exec(cmd):
    do_call("bash -c \"%s\"" % (cmd))


parser = argparse.ArgumentParser(
    description="SSCE jemalloc module auto builder")
parser.add_argument('--prebuilt', dest='prebuilt', action='store_true')
args = parser.parse_args()


if args.prebuilt:
    url = "https://sima214.me/ssce/binaries/%s/%s/%s" % (
        "x86_64", "windows", "jemalloc")
    if not os.path.exists(INSTALL_DIR):
        os.makedirs(INSTALL_DIR)
    dest_path = os.path.join(INSTALL_DIR, "jemalloc.7z")
    with urllib.request.urlopen(url) as r, open(dest_path, 'wb') as f:
        shutil.copyfileobj(r, f)
    do_call("7z e -y -o%s %s" % (INSTALL_DIR.replace('\\', '/'), dest_path.replace('\\', '/')))
    sys.exit(0)


if os.name != 'nt' and is_clang():
    os.environ["CFLAGS"] = "%s %s %s" % (
        os.environ.get("CFLAGS", ""),
        " ".join(EXTRA_FLAGS),
        " ".join(CLANG_LTO_FLAGS))
    os.environ["CXXFLAGS"] = "%s %s %s" % (
        os.environ.get("CXXFLAGS", ""),
        " ".join(EXTRA_FLAGS),
        " ".join(CLANG_LTO_FLAGS))
    os.environ["LDFLAGS"] = "%s %s" % (
        os.environ.get("LDFLAGS", ""),
        " ".join(CLANG_LTO_FLAGS))
else:
    os.environ["CFLAGS"] = "%s %s %s" % (
        os.environ.get("CFLAGS", ""),
        " ".join(EXTRA_FLAGS),
        " ".join(GCC_LTO_FLAGS))
    os.environ["CXXFLAGS"] = "%s %s %s" % (
        os.environ.get("CXXFLAGS", ""),
        " ".join(EXTRA_FLAGS),
        " ".join(GCC_LTO_FLAGS))
    os.environ["LDFLAGS"] = "%s %s" % (
        os.environ.get("LDFLAGS", ""),
        " ".join(GCC_LTO_FLAGS))

old_path = os.environ["PATH"]
if os.name == 'nt':
    os.environ["PATH"] = os.environ["MSYS_PATH"] + ";" + os.environ["PATH"]
shell_exec("autoconf")
if not os.path.isdir(BUILD_DIR):
    os.mkdir(BUILD_DIR)
os.chdir(BUILD_DIR)
shell_exec("../configure " + " ".join(CONFIG_FLAGS).replace('\\', '/'))
if os.name == 'nt':
    os.environ["PATH"] = old_path
do_call("%s -j %d" % (MAKE_COMMAND, cpu_count()))
do_call("%s %s %s" % (MAKE_COMMAND, "install_include", "install_lib"))
shutil.move(os.path.join(INSTALL_DIR, os.path.join(
    "jemalloc", "jemalloc.h")), os.path.join(INSTALL_DIR, "jemalloc.h"))
