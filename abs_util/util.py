import os
import platform
import subprocess
from typing import List, Optional
from colorama import Fore, Style
from prompt_toolkit.shortcuts import prompt
from prompt_toolkit.styles import Style as tk_Style
from prompt_toolkit.output import ColorDepth
from platformdirs import user_config_dir


def get_config_file_path():
    return os.path.join(
        user_config_dir(
            appname='abs_util',
            appauthor='teekeks',
            ensure_exists=True),
        'config.json')


def check_setup(args, cfg) -> List[str]:
    caps = []
    if cfg.get('server') is not None:
        if args.user is not None and args.password is not None:
            caps.append('base-setup')
    if args.library is not None:
        caps.append('library')
    if args.kobo_dir is not None:
        caps.append('kdir')
    if args.library_dir is not None:
        caps.append('libdir')
    return caps


def add_default_args(sub_parser, cfg, target, required_override: Optional[bool] = None):
    if target == 'base-api':
        sub_parser.add_argument('-s', '--server', help='Audiobookshelf Server URL', default=cfg.get('server'),
                                required=False if required_override is None else required_override)
        sub_parser.add_argument('-u', '--user', help='Audiobookshelf User', default=cfg.get('user'),
                                required=False if required_override is None else required_override)
        sub_parser.add_argument('-p', '--password', help='Audiobookshelf Password', default=cfg.get('password'),
                                required=False if required_override is None else required_override)
    if target == 'library':
        sub_parser.add_argument('-l', '--library', default=cfg.get('library'), help='The Audiobookshelf library to target',
                                required=False if required_override is None else required_override)
    if target == 'kobo-dir':
        sub_parser.add_argument('-kdir', '--kobo-dir', help='The Directory your Kobo Reader is mounted to',
                                required=True if required_override is None else required_override)


def open_path(path):
    if platform.system() == 'Darwin':
        subprocess.call(('open', path))
    elif platform.system() == 'Windows':
        os.startfile(path)
    else:
        subprocess.call(('xdg-open', path))


def request_prompt(question: str, default: Optional[str] = None) -> str:
    style = tk_Style.from_dict({
        '': '#ff0066',
        'question': 'ansicyan',
        'pound': '#00aa00',
        'default': '#666666',
        'current': '#666666'
    })
    if default is None:
        message = [
            ('class:question', f'{question}'),
            ('class:pound', ': ')
        ]
        return prompt(message, style=style, color_depth=ColorDepth.TRUE_COLOR)
    else:
        message = [
            ('class:question', f'{question} '),
            ('class:current', f'[{default}]'),
            ('class:pound', ': ')
        ]

        answer = prompt(message, style=style, color_depth=ColorDepth.TRUE_COLOR)
        return answer if len(answer) > 0 else default


def display_error(msg: str) -> None:
    print(f'{Fore.RED}ERROR: {msg}{Style.RESET_ALL}')
    pass
