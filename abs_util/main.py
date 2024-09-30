import json
import argparse
import colorama
import os

from abs_util.actions.setup import setup_parser
from abs_util.actions.clear_authors import clear_authors_parser
from abs_util.actions.kobo_sync import kobo_sync_parser
from abs_util.actions.folder_from_goodreads import from_goodreads_parser


def run():
    colorama.init(autoreset=True)

    if not os.path.isfile('..config.json'):
        with open('..config.json', 'w') as _f:
            json.dump({}, _f)

    with open('../config.json') as _f:
        cfg = json.load(_f)

    parser = argparse.ArgumentParser(description='Audiobookshelf Utility',
                                     prog='python -m abs_util',
                                     formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=100, width=400))

    sub_parser = parser.add_subparsers(dest='action', title='actions', description='All actions supported by abs_util', metavar='action')

    setup_parser(sub_parser, cfg)
    clear_authors_parser(sub_parser, cfg)
    from_goodreads_parser(sub_parser, cfg)
    kobo_sync_parser(sub_parser, cfg)

    args = parser.parse_args()
    args.func(args, cfg)
