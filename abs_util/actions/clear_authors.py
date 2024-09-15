import argparse
import asyncio
from colorama import Fore, Style

from audiobookshelf.client import ABSClient
from abs_util.util import display_error, add_default_args


async def clear_authors(args):
    client = ABSClient(args.server)
    await client.authorize(args.user, args.password)
    libs = await client.get_libraries()
    lib_filter = args.library
    found_filter = lib_filter is None
    for lib in libs:
        if lib_filter is not None and not lib['name'].lower() == lib_filter.lower():
            continue
        found_filter = True
        print(f'{Fore.LIGHTCYAN_EX}Checking authors for library {Fore.GREEN}{lib["name"]}{Fore.LIGHTCYAN_EX}...{Style.RESET_ALL}')
        authors = await client.get_library_authors(lib['id'])
        for author in authors:
            if author['numBooks'] == 0:
                print(f'{Fore.LIGHTCYAN_EX}- removed author {Fore.GREEN}{author["name"]}{Fore.LIGHTCYAN_EX}: has no books{Style.RESET_ALL}')
                await client.delete_author(author['id'])
    if not found_filter:
        display_error(f'"{lib_filter}" is not a valid library!')


def clear_authors_action(args, cfg):
    asyncio.run(clear_authors(args))


def clear_authors_parser(sub_parser, cfg: dict):
    parser = sub_parser.add_parser('clear-authors', help='Remove authors with no books from either all or selected libraries',
                                   formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=100, width=360))
    parser.set_defaults(func=clear_authors_action)
    add_default_args(parser, cfg, 'base-api')
    add_default_args(parser, cfg, 'library')
