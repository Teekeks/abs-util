import argparse
import json

from prompt_toolkit.shortcuts import prompt
from prompt_toolkit.styles import Style
from prompt_toolkit.output import ColorDepth

from abs_util.util import add_default_args


def setup_action(args, cfg):
    stype = Style.from_dict({
        '': '#ff0066',
        'question': 'ansicyan',
        'pound': '#00aa00',
        'default': '#666666',
        'current': '#666666'
    })
    message = [
        ('class:question', 'Server URL '),
        ('class:current', f'[{args.server}]'),
        ('class:pound', ': ')
    ]
    server = prompt(message, style=stype, color_depth=ColorDepth.TRUE_COLOR)
    message = [
        ('class:question', 'User '),
        ('class:current', f'[{args.user}]'),
        ('class:pound', ': ')
    ]
    user = prompt(message, style=stype, color_depth=ColorDepth.TRUE_COLOR)
    message = [
        ('class:question', 'Change Password (Y/N) '),
        ('class:current', f'[N]'),
        ('class:pound', ': ')
    ]
    change_pwd = prompt(message, style=stype, color_depth=ColorDepth.TRUE_COLOR)
    password = ''
    if change_pwd.lower() == 'y':
        message = [
            ('class:question', 'Password'),
            ('class:pound', ': ')
        ]
        password = prompt(message, style=stype, color_depth=ColorDepth.TRUE_COLOR)

    with open('config.json', 'w') as _f:
        json.dump({
            'server': server if len(server) > 0 else args.server,
            'user': user if len(user) > 0 else args.user,
            'password': password if len(password) > 0 else args.password
        }, _f)


def setup_parser(sub_parser, cfg: dict):
    parser = sub_parser.add_parser('setup', help='Setup basic settings',
                                   formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=100, width=360))
    parser.set_defaults(func=setup_action)
    add_default_args(parser, cfg, 'base-api')
