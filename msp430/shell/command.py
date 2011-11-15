#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2010 Chris Liechti <cliechti@gmx.net>
# All Rights Reserved.
# Simplified BSD License (see LICENSE.txt for full text)
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
            raise OSError("target '%s' is not a directory" % (dest,))
    # use imap because it terminates at the end of the shortest iterable
    for _ in itertools.imap(shutil.copy, paths, itertools.repeat(dest)):
        pass

def _rm_path(path, force=False, recursive=False):
    if not os.path.exists(path):
        if force:
            return # rm -f ignores missing paths
        else:
            raise OSError('no such file or directory: %s' % (path,))
    elif not is_writeable(path):
        if force:
            # make file writeable in order to be able to delete it
            os.chmod(path, stat.S_IWRITE)
        else:
            raise OSError('cannot rm write-protected file or directory: %s' % (path,))
    if os.path.isdir(path):
        if not recursive:
            raise OSError("cannot remove directory: %s" % (path,))
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
            raise OSError("no such file or directory: '%s'" % (dest,))
        if not os.path.isdir(dest):
            raise OSError("target '%s' is not a directory" % (dest,))
    for path in paths:
        if not os.path.exists(path):
            raise OSError('no such file or directory: %s' % (path,))
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
                raise OSError("can't touch write-protected path: %s" % (path,))
        else:
            open(path, 'w').close()

def is_writeable(path):
    """\
    Return True if the path is writeable by all of the populations
    specified, False otherwise.
    """
    if os.path.exists(path):
        return (os.stat(path).st_mode & (stat.S_IWUSR|stat.S_IWGRP|stat.S_IWOTH)) != 0
    raise OSError('no such file or directory: %s' % (path,))

#############################################

import optparse
import sys
import os


def command_cat(parser, argv):
    """show file contents"""
    (options, args) = parser.parse_args(argv)
    for path in expanded(args):
        if path == '-':
            try:
                for line in sys.stdin:
                    if not line: break
                    sys.stdout.write(line)
            except KeyboardInterrupt:
                pass
        else:
            f = open(path)
            for line in f:
                sys.stdout.write(line)
            f.close()


def command_true(parser, argv):
    (options, args) = parser.parse_args(argv)
    return 0


def command_false(parser, argv):
    (options, args) = parser.parse_args(argv)
    return 1


def command_expand(parser, argv):
    (options, args) = parser.parse_args(argv)
    sys.stdout.write(' '.join(expanded(args)))
    sys.stdout.write('\n')


def command_rm(parser, argv):
    parser.add_option("-r", "--recursive",
        dest = "recursive",
        help = "Delete subdirectories too.",
        default = False,
        action = 'store_true'
    )
    parser.add_option("-f", "--force",
        dest = "force",
        help = "Ignore missing, also delete write protected files.",
        default = False,
        action = 'store_true'
    )
    (options, args) = parser.parse_args(argv)

    rm(expanded(args), options.force, options.recursive)


def command_mkdir(parser, argv):
    parser.add_option("-p",
        dest = "create_missing",
        help = "Create any missing intermediate pathname components.",
        default = False,
        action = 'store_true'
    )
    (options, args) = parser.parse_args(argv)

    if not args:
        parser.error('Expected DIRECTORY')

    for path in args:
        mkdir(path, options.create_missing)


def command_touch(parser, argv):
    """update file date"""
    (options, args) = parser.parse_args(argv)
    touch(expanded(args))


def command_cp(parser, argv):
    """copy files"""
    parser.add_option("-t", "--target-directory",
        dest = "target_directory",
        help = "Copy all SOURCE arguments into DIRECTORY.",
        default = None,
        metavar = "DIRECTORY"
    )
    (options, args) = parser.parse_args(argv)
    if options.target_directory:
        target = options.target_directory
    else:
        if len(args) < 2:
            parser.error('Expected at least one SOURCE and DESTINATION argument')
        target = args.pop()
    if not args:
        parser.error('Missing SOURCE')
    cp(expanded(args), target)


def command_mv(parser, argv):
    """move or rename files"""
    parser.add_option("-f", "--force",
        dest = "force",
        help = "Do not ask any questions. (ignored)",
        default = False,
        action = 'store_true'
    )
    (options, args) = parser.parse_args(argv)
    if len(args) < 2:
        parser.error('Expected at least one SOURCE and TARGET argument.')
    target = args.pop()
    mv(expanded(args), target)


def command_which(parser, argv):
    """find files on PATH"""
    parser.add_option("-v", "--verbose",
        dest = "stop_first",
        help = "Show all hits (default: stop after 1st).",
        default = True,
        action = 'store_false'
    )
    (options, args) = parser.parse_args(argv)
    path = os.environ['PATH'].split(os.pathsep)
    for filename in args:
        for location in path:
            p = os.path.join(location, filename)
            if os.path.exists(p):
                sys.stdout.write('%s\n' % p)
                if options.stop_first: return


def command_list(parser, argv):
    sys.stderr.write('Command collection:\n')
    for name, (command, help, usage) in sorted(COMMANDS.items()):
        sys.stderr.write('- %-7s %s\n' % (name, help))
    sys.stderr.write('\nMore help with "%s COMMAND --help"\n' % (os.path.basename(sys.argv[0]),))


COMMANDS = {
        'cat': (command_cat,     'Show file contents.',            '%prog [-|FILE]...'),
        'cp': (command_cp,       'Copy files.',                    '%prog SOURCE... DESTINATION\n       %prog -t DIRECTORY SOURCE...'),
        'expand': (command_expand, 'Expand globbing patterns.',    '%prog [PATH...]'),
        'false': (command_false, 'Simply return exit code 1',      '%prog'),
        'mkdir': (command_mkdir, 'Create directories.',            '%prog [-p] DIRECTORY'),
        'mv': (command_mv,       'Move/rename files.',             '%prog [options] SOURCE... TARGET'),
        'rm': (command_rm,       'Delete files/directories.',      '%prog [options] FILE...'),
        'true': (command_true,   'Simply return exit code 0',      '%prog'),
        'touch': (command_touch, 'Update file date, create file.', '%prog [options] FILE...'),
        'list': (command_list,   'This text.',                     '%prog'),
        'which': (command_which, 'Find files in teh PATH',         '%prog [options] FILE...'),
        }

def main():
    debug = False
    if len(sys.argv) > 1 and sys.argv[1] == '--debug':
        del sys.argv[1]
        debug = True

    if len(sys.argv) >= 2 and sys.argv[1][0] != '-':
        name = sys.argv[1]
        args = sys.argv[2:]
    else:
        name = 'list'
        args = sys.argv[1:]

    try:
        command, help, usage = COMMANDS[name]
    except KeyError:
        sys.stderr.write('ERROR: No such command implemented: %s' % (name,))
        sys.exit(1)

    parser = optparse.OptionParser(usage=usage, prog=name)
    try:
        result = command(parser, args)
        if result is None: result = 0
        sys.exit(result)
    except Exception, e:
        if debug: raise
        sys.stderr.write('ERROR: %s\n' % (e,))
        sys.exit(1)
    parser.error('Expected command name, try "list".')

if __name__ == '__main__':
    main()

