#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of https://github.com/zsquareplusc/python-msp430-tools
# (C) 2010 Chris Liechti <cliechti@gmx.net>
#
# SPDX-License-Identifier:    BSD-3-Clause
#
# parts based on clutchski@gmail.com ' fileutils.py (which is public domain).
"""\
Implement POSIX like commands such as cp, mv, rm, ...
"""

import itertools
import os
import shutil
import stat
import glob
import argparse
import sys


def expanded(paths):
    """expand each element of a list of paths with globbing patterns"""
    for path1 in paths:
        if '*' in path1 or '?' in path1 or '[' in path1:
            for path in glob.iglob(path1):
                yield path
        else:
            yield path1


def mkdir(path, create_missing=False):
    """Create the given directory"""
    if create_missing:
        if not os.path.exists(path):
            os.makedirs(path)
        else:
            if not os.path.isdir(path):
                raise OSError('path exists but is not a directory')
    else:
        os.mkdir(path)


def cp(paths, dest):
    """\
    Copy the given file or list of files to the destination. When copying
    more than one file, the destination must be a directory.
    """
    paths = list(paths)   # convert generator/iterator -> list
    if len(paths) > 1:
        if not os.path.exists(dest) or not os.path.isdir(dest):
            raise OSError('target "{}" is not a directory'.format(dest))
    # use imap because it terminates at the end of the shortest iterable
    for _ in itertools.imap(shutil.copy, paths, itertools.repeat(dest)):
        pass


def _rm_path(path, force=False, recursive=False):
    if not os.path.exists(path):
        if force:
            return  # rm -f ignores missing paths
        else:
            raise OSError('no such file or directory: {}'.format(path))
    elif not is_writeable(path):
        if force:
            # make file writeable in order to be able to delete it
            os.chmod(path, stat.S_IWRITE)
        else:
            raise OSError('cannot rm write-protected file or directory: {}'.format(path))
    if os.path.isdir(path):
        if not recursive:
            raise OSError('cannot remove directory: {}'.format(path))
        for child_path in os.listdir(path):
            rm(os.path.join(path, child_path), force, recursive)
        os.rmdir(path)
    else:
        os.remove(path)


def rm(paths, force=False, recursive=False):
    """Remove the given file or list of files."""
    for path in paths:
        _rm_path(path, force, recursive)


def mv(paths, dest):
    """\
    Move the given files or directories to the destination path. If more
    that one element is being moved, the destination must be a directory.
    """
    paths = list(paths)   # convert generator/iterator -> list
    if len(paths) > 1:
        if not os.path.exists(dest):
            raise OSError('no such file or directory: "{}"'.format(dest))
        if not os.path.isdir(dest):
            raise OSError('target "{}" is not a directory'.format(dest))
    for path in paths:
        if not os.path.exists(path):
            raise OSError('no such file or directory: {}'.format(path))
        shutil.move(path, dest)


def touch(paths):
    """\
    Update the access and modification times of the given path or list of
    paths. Any non-existent files will be created.
    """
    for path in paths:
        if os.path.exists(path):
            if is_writeable(path):
                os.utime(path, None)
            else:
                raise OSError('can not touch write-protected path: {}'.format(path))
        else:
            open(path, 'w').close()


def is_writeable(path):
    """\
    Return True if the path is writeable by all of the populations
    specified, False otherwise.
    """
    if os.path.exists(path):
        return (os.stat(path).st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)) != 0
    raise OSError('no such file or directory: {}'.format(path))


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
class Commandlet(object):
    """helper for a bunch of small "commandlets" """
    name = None

    def __init__(self):
        self.parser = argparse.ArgumentParser(prog=self.name)
        self.args = None

    def parse_args(self, args):
        """add remaining arguments and parse sys.argv"""
        self.parser.add_argument(
            '--develop',
            action='store_true',
            help='show tracebacks on errors (development of this tool)')

        self.args = self.parser.parse_args(args)
        return self.args

    def main(self, args):
        """main that builds the argument parser, calls run() and handles errors"""
        try:
            self.configure_parser()
            self.parse_args(args)
            exit_code = self.run(self.args)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            sys.stderr.write('User aborted.\n')
            sys.exit(1)
        except Exception as msg:
            if self.args is None or self.args.develop:
                raise
            sys.stderr.write('\nAn error occurred:\n{}\n'.format(msg))
            sys.exit(2)
        else:
            sys.exit(exit_code)

    # ----- override in subclass -----

    def configure_parser(self):
        """update the argument parser here"""

    def run(self):
        """override this in actual tool"""


class Cat(Commandlet):
    """Show file contents."""
    name = 'cat'

    def configure_parser(self):
        self.parser.add_argument(
            'FILE',
            nargs='*',
            help='filename or "-" for stdin')

    def run(self, args):
        for path in expanded(args.FILE):
            for line in argparse.FileType('r')(path):
                sys.stdout.write(line)


class Truly(Commandlet):
    """Simply return exit code 0"""
    name = 'true'

    def run(self, args):
        return 0


class Falsly(Commandlet):
    """Simply return exit code 1"""
    name = 'false'

    def run(self, args):
        return 1


class Expand(Commandlet):
    """Expand globbing patterns."""
    name = 'expand'

    def configure_parser(self):
        self.parser.add_argument('PATTERN', nargs='*')

    def run(self, args):
        sys.stdout.write(' '.join(expanded(args.PATTERN)))
        sys.stdout.write('\n')


class Remove(Commandlet):
    """Delete files/directories."""
    name = 'rm'

    def configure_parser(self):
        self.parser.add_argument('PATH', nargs='*')
        self.parser.add_argument(
            '-r', '--recursive',
            help='Delete subdirectories too.',
            default=False,
            action='store_true')
        self.parser.add_argument(
            '-f', '--force',
            help='Ignore missing, also delete write protected files.',
            default=False,
            action='store_true')

    def run(self, args):
        rm(expanded(args.PATH), args.force, args.recursive)


class Makedir(Commandlet):
    """Create directories."""
    name = 'mkdir'

    def configure_parser(self):
        self.parser.add_argument('DIRECTORY', nargs='+')
        self.parser.add_argument(
            '-p',
            dest='create_missing',
            help='Create any missing intermediate pathname components.',
            default=False,
            action='store_true')

    def run(self, args):
        for path in args.DIRECTORY:
            mkdir(path, args.create_missing)


class Touch(Commandlet):
    """Update file date, create file."""
    name = 'touch'

    def configure_parser(self):
        self.parser.add_argument('PATH', nargs='+')

    def run(self, args):
        touch(expanded(args.PATH))


class Copy(Commandlet):
    """Copy files."""
    name = 'cp'

    def configure_parser(self):
        self.parser.add_argument('SRC', nargs='+')
        self.parser.add_argument('DST', nargs='?')
        self.parser.add_argument(
            '-t', '--target-directory',
            help='Copy all SRC arguments into DIRECTORY.',
            metavar="DIRECTORY")

    def run(self, args):
        if args.target_directory:
            args.DST = args.target_directory
        else:
            args.DST = args.SRC.pop(-1)
        cp(expanded(args.SRC), args.DST)


class Move(Commandlet):
    """Move/rename files."""
    name = 'mv'

    def configure_parser(self):
        self.parser.add_argument('SRC', nargs='+')
        self.parser.add_argument('DST', nargs=1)
        self.parser.add_argument(
            '-f', '--force',
            help='Do not ask any questions. (ignored)',
            default=False,
            action='store_true')

    def run(self, args):
        mv(expanded(args.SRC), args.DST)


class Which(Commandlet):
    """Find files in teh PATH."""
    name = 'which'

    def configure_parser(self):
        self.parser.add_argument('NAME', nargs='+')
        self.parser.add_argument(
            '-v', '--verbose',
            dest='stop_first',
            help='Show all hits (default: stop after 1st).',
            default=True,
            action='store_false')

    def run(self, args):
        path = os.environ['PATH'].split(os.pathsep)
        if sys.platform.startswith('win'):
            # windows implicitly searches the current dir too
            path.insert(0, '.')
        for name in args.NAME:
            names = [name]
            # windows not only finds the name it also finds it with several
            # different extensions, need to check these too...
            if sys.platform.startswith('win'):
                try:
                    extensions = os.environ['PATHEXT'].split(os.pathsep)
                    names.extend(['{}{}'.format(name, ext) for ext in extensions])
                except KeyError:
                    sys.stderr.write('Warning, environment variable PATHEXT not set!\n')
            # for each name search through the path
            for filename in names:
                for location in path:
                    p = os.path.join(location, filename)
                    if os.path.exists(p):
                        sys.stdout.write('{}\n'.format(p))
                        if args.stop_first:
                            return


class List(Commandlet):
    """List subcommands of this tool."""
    name = 'list'

    def run(self, args):
        sys.stderr.write('Command collection:\n')
        for name, command_class in sorted(COMMANDS.items()):
            sys.stderr.write('- {:<7} {}\n'.format(name, command_class.__doc__))
        sys.stderr.write('\nMore help with "{} COMMAND --help"\n'.format(os.path.basename(sys.argv[0])))


# automatically find all commands, exclude base class
COMMANDS = {c.name: c for c in globals().values()
                      if type(c) is type and
                         issubclass(c, Commandlet) and
                         c.name is not None}


def main():
    if len(sys.argv) >= 2:
        name = sys.argv[1]
        args = sys.argv[2:]
    else:
        name = 'list'
        args = sys.argv[1:]

    try:
        command_class = COMMANDS[name]
    except KeyError:
        sys.stderr.write('ERROR: No such command implemented: {}\n'.format(name))
        sys.exit(1)

    command_class().main(args)


if __name__ == '__main__':
    main()
