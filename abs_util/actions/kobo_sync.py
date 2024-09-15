import argparse
import asyncio
import sys
import os
from collections import namedtuple
from typing import List

from audiobookshelf import ABSClient
from colorama import Fore, Style
from abs_util.util import display_error, add_default_args
from pprint import pprint
import json
import shutil
import aiosqlite


BookRecord = namedtuple('Book', ['title', 'subtitle', 'author', 'description', 'series', 'series_number',
                                 'series_number_float', 'series_id', 'read_status'])


async def get_target_lib(args, client: ABSClient) -> dict:
    """Find valid target library and return"""
    libs = await client.get_libraries()
    for lib in libs:
        if lib['name'].lower() == args.library.lower():
            if lib['mediaType'] != 'book':
                display_error(f'Library {lib["name"]} is not of type book.')
                sys.exit(1)
            return lib
    display_error(f'Library {args.library} not found.')
    sys.exit(1)


def build_kobo_tree(args, target_lib) -> List[dict]:
    print(f'{Fore.LIGHTCYAN_EX}Building kobo reader tree...{Style.RESET_ALL}')
    _found = []
    if not os.path.isdir(args.kobo_dir):
        display_error(f'Kobo mount directory "{args.kobo_dir}" does not exists')
        sys.exit(1)
    lib_dir = str(os.path.join(args.kobo_dir, 'abs-library', target_lib['id']))
    if not os.path.isdir(lib_dir):
        # library does not exists yet
        return []
    for root, dirs, files in os.walk(lib_dir):
        for filename in files:
            if filename.lower().endswith('abs-item.json'):
                with open(os.path.join(root, filename), 'r') as _f:
                    item_data = json.load(_f)
                item_dir = os.path.dirname(os.path.join(root, filename))
                _found.append({'id': item_data['id'], 'folder': item_dir})
    return _found
    pass


async def sync_item(args, client: ABSClient, target_lib, item: dict):
    title = item['media']['metadata']['title']
    author = item['media']['metadata']['authorName']
    print(f'{Fore.LIGHTCYAN_EX}- Syncing missing item {Fore.GREEN}{item['id']}{Fore.LIGHTCYAN_EX} - '
          f'{Fore.LIGHTGREEN_EX}{title}{Fore.LIGHTCYAN_EX} by {Fore.LIGHTGREEN_EX}{author}{Fore.LIGHTCYAN_EX} to kobo reader')
    item_dir = str(os.path.join(args.kobo_dir, 'abs-library', target_lib['id'], item['relPath']))
    if not os.path.exists(item_dir):
        os.makedirs(item_dir)
    item_data = await client.get_library_item(item['id'])
    # write item data
    with open(os.path.join(item_dir, 'abs-item.json'), 'w') as _f:
        json.dump({
            'id': item['id'],
        }, _f)
    efile = item_data['media']['ebookFile']
    target_file_path = os.path.join(item_dir, efile['metadata']['relPath'])
    await client.download_file(item_data['media']['libraryItemId'], efile['ino'], str(target_file_path))


async def remove_item(item: dict):
    print(f'{Fore.LIGHTCYAN_EX}- Removing unexpected item {Fore.GREEN}{item['id']}{Fore.LIGHTCYAN_EX} from {Fore.GREEN}{item['folder']}')
    shutil.rmtree(item['folder'])


async def sync_metadata(args, client: ABSClient, db, target_lib, item, kobo_item):
    item_data = await client.get_library_item(item['id'], include=['progress', 'authors'], expanded=True)
    efile = item_data['media']['ebookFile']
    item_id = f'file:///mnt/onboard/abs-library/{target_lib['id']}/{item['relPath']}/{efile['metadata']['relPath']}'
    current_status: BookRecord = None
    async with db.execute('SELECT Title, Subtitle, Attribution, Description, Series, SeriesNumber, SeriesNumberFloat, SeriesID, ReadStatus '
                          'FROM content WHERE ContentID == ? AND ContentType == 6', (item_id,)) as cursor:
        async for row in cursor:
            current_status = BookRecord._make(row)
    if current_status is not None:
        is_same = True
        metadata = item_data['media']['metadata']
        is_same &= current_status.title == metadata['title']
        is_same &= current_status.subtitle == metadata['subtitle']
        is_same &= current_status.author == metadata['authorName']
        is_same &= current_status.description == metadata['description']
        if len(metadata['series']) > 0:
            is_same &= current_status.series == metadata['series'][0]['name']
            is_same &= current_status.series_number == metadata['series'][0]['sequence']
            is_same &= current_status.series_id == metadata['series'][0]['id']
            is_same &= current_status.series_number_float == float(metadata['series'][0]['sequence'])
        update_status = False
        if not args.no_progress_sync:
            if item_data.get('userMediaProgress') is not None and item_data['userMediaProgress']['isFinished'] and current_status.read_status != 2:
                is_same = False
                update_status = True
        # temp
        if not is_same:
            print(f'{Fore.LIGHTCYAN_EX}- Syncing metadata and reading progress for item {Fore.GREEN}{item['id']}')
        if not is_same:
            payload = (
                metadata['title'],
                metadata['subtitle'],
                metadata['authorName'],
                metadata['description'],
            )
            if len(metadata['series']) > 0:
                payload += (metadata['series'][0]['name'],
                            metadata['series'][0]['sequence'],
                            float(metadata['series'][0]['sequence']),
                            metadata['series'][0]['id'])
            else:
                payload += (None, None, None, None)
            if update_status:
                payload += (2 if item_data['userMediaProgress']['isFinished'] else current_status.read_status,)
            status_query = ('UPDATE content SET Title = ?, Subtitle = ?, Attribution = ?, Description = ?, Series = ?, SeriesNumber = ?, '
                            'SeriesNumberFloat = ?, SeriesID = ?, ReadStatus = ? WHERE ContentID = ?')
            metadata_query = ('UPDATE content SET Title = ?, Subtitle = ?, Attribution = ?, Description = ?, Series = ?, SeriesNumber = ?, '
                              'SeriesNumberFloat = ?, SeriesID = ? WHERE ContentID = ?')
            await db.execute(status_query if update_status else metadata_query, payload + (item_id,))
            await db.commit()


async def kobo_sync(args):
    client = ABSClient(args.server)
    await client.authorize(args.user, args.password)
    db = await aiosqlite.connect(str(os.path.join(args.kobo_dir, '.kobo', 'KoboReader.sqlite')))
    target_lib = await get_target_lib(args, client)
    print(f'{Fore.LIGHTCYAN_EX}Collect all items from library {Fore.GREEN}{target_lib["name"]}{Fore.LIGHTCYAN_EX}...')
    lib_items = await client.get_library_items(target_lib['id'], limit=0)
    print(f'{Fore.LIGHTCYAN_EX}Found {Fore.GREEN}{lib_items["total"]}{Fore.LIGHTCYAN_EX} items in audiobookshelf')
    lib_items = {d['id']: d for d in lib_items['results']}
    kobo_items = build_kobo_tree(args, target_lib)
    print(f'{Fore.LIGHTCYAN_EX}Found {Fore.GREEN}{len(kobo_items)}{Fore.LIGHTCYAN_EX} items on kobo reader')
    kobo_item_ids = [k['id'] for k in kobo_items]
    # TODO check if existing kobo items are up to date
    unexpected_items = [i for i in kobo_items if i['id'] not in lib_items.keys()]
    if len(unexpected_items) > 0:
        print(f'{Fore.LIGHTCYAN_EX}Found {Fore.GREEN}{len(unexpected_items)}{Fore.LIGHTCYAN_EX} unexpected '
              f'item{'s' if len(unexpected_items) > 1 else ''} on kobo reader:')
        for item in unexpected_items:
            await remove_item(item)
    else:
        print(f'{Fore.LIGHTCYAN_EX}No unexpected items on kobo reader')
    missing_items = [d for i, d in lib_items.items() if i not in kobo_item_ids]
    if len(missing_items) > 0:
        print(f'{Fore.LIGHTCYAN_EX}Found {Fore.GREEN}{len(missing_items)}{Fore.LIGHTCYAN_EX} item{'s' if len(missing_items) > 1 else ''} '
              f'missing from kobo reader:')
    else:
        print(f'{Fore.LIGHTCYAN_EX}No items missing from kobo reader')
    for missing_item in missing_items:
        await sync_item(args, client, target_lib, missing_item)
    # sync metadata and progress of existing items
    print(f'{Fore.LIGHTCYAN_EX}Syncing metadata and progress of previously existing items...')
    for kobo_item in kobo_items:
        await sync_metadata(args, client, db, target_lib, lib_items[kobo_item['id']], kobo_item)
    # TODO sync progress kobo -> abs
    await db.close()
    print(f'{Fore.GREEN}Done{Style.RESET_ALL}')


def kobo_sync_action(args, cfg):
    asyncio.run(kobo_sync(args))


def kobo_sync_parser(sub_parser, cfg):
    parser = sub_parser.add_parser('kobo-sync', help='Sync a library with a USB connected Kobo Reader',
                                   formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=100, width=360))
    parser.set_defaults(func=kobo_sync_action)
    add_default_args(parser, cfg, 'library', required_override=True)
    add_default_args(parser, cfg, 'kobo-dir')
    add_default_args(parser, cfg, 'base-api')
    parser.add_argument('--no-progress-sync', action='store_true', default=False, help='Do not sync reading progress')

