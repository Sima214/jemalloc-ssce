#!/usr/bin/env python

from multiprocessing import cpu_count
from shlex import split as cmdsplit
import subprocess
import sys
import os


JEMALLOC_PREFIX = "je_"

SOURCE_DIR = os.path.realpath(os.path.dirname(os.path.realpath(__file__)))

BUILD_DIR = SOURCE_DIR + "/build"

INSTALL_DIR = SOURCE_DIR + "/install"

CONFIG_FLAGS = [
    "--disable-cxx", "--disable-shared",
    "--with-jemalloc-prefix=%s" % (JEMALLOC_PREFIX),
    "--prefix=%s" % (INSTALL_DIR),
    "--libdir=%s" % (INSTALL_DIR),
    "--includedir=%s" % (INSTALL_DIR),
]

MAKE_COMMAND = "mingw32-make" if os.name == 'nt' else "make"


def do_call(arg):
    print(">" + arg, flush=True)
    args = cmdsplit(arg)
    try:
        subprocess.check_call(args, env=os.environ)
    except subprocess.CalledProcessError as error:
        print(error, flush=True)
        print(error.output, flush=True)
        sys.exit(1)


def shell_exec(cmd):
    do_call("bash -c \"%s\"" % (cmd))


shell_exec("autoconf")
if not os.path.isdir(BUILD_DIR):
    os.mkdir(BUILD_DIR)
os.chdir(BUILD_DIR)
shell_exec("../configure " + " ".join(CONFIG_FLAGS))
os.system("%s -j %d %s %s" % (MAKE_COMMAND, cpu_count(),
                              "install_include", "install_lib_static"))
