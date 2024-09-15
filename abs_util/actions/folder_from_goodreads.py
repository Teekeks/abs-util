import argparse
import asyncio
import os.path
from email.policy import default

from colorama import Fore, Style

from aiohttp import ClientSession
from bs4 import BeautifulSoup
from abs_util.util import request_prompt, open_path
import re


RE_BOOK_NUMBER = re.compile(r'^Book (\d+\.?\d*)$')

RE_FORBIDDEN_CHARS = re.compile(r'[<>:"/\\|?*]')


async def action(args, cfg):
    series_url = args.goodreads_series
    async with ClientSession() as session:
        req = await session.get(series_url)
        html = await req.text()
        soup = BeautifulSoup(html, 'html.parser')
    series_title = soup.find('div', class_='responsiveSeriesHeader__title').text
    if series_title.endswith(' Series'):
        series_title = series_title.replace(' Series', '')
    print(f'{Fore.LIGHTCYAN_EX}Found series {Fore.GREEN}{series_title}')
    author = None
    for tag in soup.find_all('div', class_='listWithDividers__item'):
        book = tag.find('h3').text
        book_nr = RE_BOOK_NUMBER.findall(book)
        if len(book_nr) == 0:
            continue
        book_nr = book_nr[0]
        title = RE_FORBIDDEN_CHARS.sub('', tag.find('span').text)
        author = RE_FORBIDDEN_CHARS.sub('', tag.find('span', {'itemprop': 'author'}).text)
        folder_name = f'{book_nr:0>2} - {title}'
        root = args.library_dir
        path = os.path.join(root, author, series_title, folder_name)
        if not os.path.exists(path):
            print(f'{Fore.LIGHTCYAN_EX}- creating folder {Fore.GREEN}{path}{Fore.LIGHTCYAN_EX}...')
            os.makedirs(path)
        else:
            print(f'{Fore.LIGHTCYAN_EX}- skipping {Fore.GREEN}{path}{Fore.LIGHTCYAN_EX}: already exists')
    if args.open_folder:
        open_path(os.path.join(args.library_dir, author, series_title))


def from_goodreads_action(args, cfg):
    if args.goodreads_series is None:
        args.goodreads_series = request_prompt('Goodreads Series URL')
    asyncio.run(action(args, cfg))


def from_goodreads_parser(sub_parser, cfg: dict):
    parser = sub_parser.add_parser('goodreads-folder-import', help='Create Folders from Goodreads Series Link',
                                   formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=100, width=360))
    parser.set_defaults(func=from_goodreads_action)
    parser.add_argument('-libdir', '--library-dir', required=True, default=cfg.get('libdir'), help='The Library base directory')
    parser.add_argument('--goodreads-series', required=False, help='The URL to a Goodreads series')
    parser.add_argument('--open-folder', required=False, action='store_true', default=False, help='Open the series folder after creating structure')
    pass
