#!/usr/bin/env python3
"""Bash completion for ase.

Put this in your .bashrc::

    complete -o default -C /path/to/ase/cli/complete.py ase

or run::

    $ ase tab-completion

"""

from __future__ import print_function
import os
import sys
from glob import glob


def match(word, *suffixes):
    return [w for w in glob(word + '*')
            if any(w.endswith(suffix) for suffix in suffixes)]


# Beginning of computer generated data:
commands = {
    'build':
        ['-M', '--magnetic-moment', '--modify', '-V', '--vacuum',
         '--unit-cell', '--bond-length', '-x',
         '--crystal-structure', '-a', '--lattice-constant',
         '--orthorhombic', '--cubic', '-r', '--repeat', '-g',
         '--gui'],
    'db':
        ['-n', '--count', '-l', '--long', '-i', '--insert-into', '-a',
         '--add-from-file', '-k', '--add-key-value-pairs', '-L',
         '--limit', '--offset', '--delete', '--delete-keys',
         '-y', '--yes', '--explain', '-c', '--columns', '-s',
         '--sort', '--cut', '-p', '--plot', '-P', '--plot-data',
         '--csv', '-w', '--open-web-browser', '--no-lock-file',
         '--analyse', '-j', '--json', '--unique'],
    'eos':
        ['-p', '--plot', '-t', '--type'],
    'gui':
        ['-n', '--image-number', '-u', '--show-unit-cell', '-r',
         '--repeat', '-R', '--rotations', '-o', '--output', '-g',
         '--graph', '-t', '--terminal', '--interpolate', '-b',
         '--bonds', '-s', '--scale'],
    'info':
        [''],
    'nomad-upload':
        ['-t', '--token', '-n', '--do-not-save-token', '-0', '--dry-run'],
    'run':
        ['-t', '--tag', '-p', '--parameters', '-d', '--database', '-S',
         '--skip', '--properties', '-f', '--maximum-force',
         '--constrain-tags', '-s', '--maximum-stress', '-E',
         '--equation-of-state', '--eos-type', '-i',
         '--interactive-python-session', '-c', '--collection',
         '--modify', '--after'],
    'tab-completion':
        ['-0', '--dry-run'],
    'test':
        ['-c', '--calculators'],
    'ulm':
        ['-n', '--index']}
# End of computer generated data


def complete(word, previous, line, point):
    for w in line[:point - len(word)].strip().split()[1:]:
        if w[0].isalpha():
            if w in commands:
                command = w
                break
    else:
        if word[:1] == '-':
            return ['-h', '--help', '-q', '--quiet', '-v', '--verbose',
                    '--version']
        return list(commands.keys()) + ['-h', '--help', '-q', '--quiet',
                                        '-v', '--verbose']

    if word[:1] == '-':
        return commands[command]

    words = []

    if command == 'db':
        if previous == 'db':
            words = match(word, '.db', '.json')

    elif command == 'run':
        if previous == 'run':
            from ase.calculators.calculator import names as words

    elif command == 'build':
        if previous in ['-x', '--crystal-structure']:
            words = ['sc', 'fcc', 'bcc', 'hcp', 'diamond', 'zincblende',
                     'rocksalt', 'cesiumchloride', 'fluorite', 'wurtzite']

    elif command == 'test':
        if previous in ['-c', '--calculator']:
            from ase.calculators.calculator import names as words

    return words


class CLICommand:
    short_description = 'Add tab-completion for Bash'

    @staticmethod
    def add_arguments(parser):
        parser.add_argument('filename', nargs='?')
        parser.add_argument('-0', '--dry-run', action='store_true')

    @staticmethod
    def run(args):
        filename = args.filename or os.path.expanduser('~/.bashrc')
        cmd = 'complete -o default -C {} ase'.format(__file__)
        print(cmd)
        if args.dry_run:
            return
        with open(filename) as fd:
            if cmd in fd.readlines():
                print('Completion script already installed!')
                return
        with open(filename, 'a') as fd:
            print(cmd, file=fd)


def update():
    """Update commands dict.

    Run this when ever options are changed::

        python3 -m ase.cli.complete

    """

    import collections
    import textwrap
    from ase.utils import import_module
    from ase.cli.main import commands

    dct = collections.defaultdict(list)

    class Subparser:
        def __init__(self, command):
            self.command = command

        def add_argument(self, *args, **kwargs):
            dct[command].extend(arg for arg in args
                                if arg.startswith('-'))

    for command, module_name in commands:
        module = import_module(module_name)
        module.CLICommand.add_arguments(Subparser(command))

    txt = 'commands = {'
    for command, opts in sorted(dct.items()):
        txt += "\n    '" + command + "':\n        ["
        txt += '\n'.join(textwrap.wrap("'" + "', '".join(opts) + "'],",
                         width=65,
                         break_on_hyphens=False,
                         subsequent_indent='         '))
    txt = txt[:-1] + '}\n'
    with open(__file__) as fd:
        lines = fd.readlines()
        a = lines.index('# Beginning of computer generated data:\n')
        b = lines.index('# End of computer generated data\n')
    lines[a + 1:b] = [txt]
    with open(__file__ + '.new', 'w') as fd:
        print(''.join(lines), end='', file=fd)
    os.rename(__file__ + '.new', __file__)
    os.chmod(__file__, 0o775)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        update()
    else:
        word, previous = sys.argv[2:]
        line = os.environ['COMP_LINE']
        point = int(os.environ['COMP_POINT'])
        words = complete(word, previous, line, point)
        for w in words:
            if w.startswith(word):
                print(w)
