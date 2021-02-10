"""
Synchronize repository metadata into a SQLite database
"""

import argparse
from datetime import datetime, timezone
import json
import sqlite3
import sys
from typing import Any, Dict, Iterator, List, Optional, Tuple

from tqdm import tqdm # type: ignore
import click
from .allrepos import ordered_crawl

def setup_database(conn: sqlite3.Connection) -> None:
    """
    Sets up a SQLite3 database to be the target of a synchronization operation. This means creating:
    - repositories table to hold repository metadata
    - history table to hold synchronization history

    Args:
    conn
        Open connection to SQLite database

    Returns: None
    """

    create_repositories = """
    CREATE TABLE IF NOT EXISTS repositories (
        github_id UNSIGNED BIG INT,
        full_name TEXT NOT NULL,
        owner TEXT NOT NULL,
        html_url TEXT NOT NULL,
        api_url TEXT NOT NULL,
        is_fork BOOLEAN
    );
    """

    create_history = """
    CREATE TABLE IF NOT EXISTS history (
        github_id UNSIGNED BIG INT NOT NULL,
        synced_at DATETIME NOT NULL
    );
    """

    c = conn.cursor()
    c.execute(create_repositories)
    c.execute(create_history)
    conn.commit()

class SyncParseError(Exception):
    """
    Returned if there was an error parsing repository metadata
    """

def parse_repository_metadata(
        result_file: str,
        metadata: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], Optional[SyncParseError]]:
    """
    Parses repository metadata into format used for synchronization

    Args:
    result_file
        Crawl result file from which metadata was extracted
    metadata
        Raw repository metadata as returned by the GitHub API repistories endpoint (for an
        individual item)

    Returns: Ordered pair with a JSON-serializable dictionary and an optional error.
    """
    parsed_metadata: Dict[str, Any] = {}
    if metadata is None:
        return (
            parsed_metadata,
            SyncParseError('Corruption: {} - Received None as metadata'.format(result_file)),
        )

    try:
        parsed_metadata['id'] = metadata['id']
        parsed_metadata['full_name'] = metadata['full_name']
        parsed_metadata['owner_login'] = metadata['owner']['login']
        parsed_metadata['html_url'] = metadata['html_url']
        parsed_metadata['url'] = metadata['url']
        parsed_metadata['fork'] = metadata['fork']
    except Exception as err:
        return (
            parsed_metadata,
            SyncParseError('Corruption: {} - {}'.format(result_file, repr(err))),
        )

    return parsed_metadata, None

def unsynced_results(
        conn: sqlite3.Connection,
        results: List[Tuple[str, int]]
    ) -> Iterator[Tuple[Dict[str, Any], Optional[SyncParseError]]]:
    """
    Given a sorted list of items in a crawl directory (as returned by allrepos.ordered_crawl),
    iterates over the entries that need to be synchronized into the given database.

    Args:
    conn
        Open connection to SQLite database
    results
        Results as returned by allrepos.ordered_crawl

    Yields: Dictionaries representing individual repositories to be synchronized into database
    """
    last_id = -1
    c = conn.cursor()
    selector = 'SELECT MAX(github_id) FROM history;'
    c.execute(selector)
    r = c.fetchone()
    if r[0] is not None:
        last_id = r[0]

    cutoff = -1
    for i, result in enumerate(results):
        if result[1] <= last_id:
            cutoff = i
        else:
            break

    if cutoff > -1:
        result_file, _ = results[cutoff]
        with open(result_file, 'r') as ifp:
            crawl_result = json.load(ifp)
        data = crawl_result.get('data', [])
        for item in data:
            if item.get('id', -1) > last_id:
                yield parse_repository_metadata(result_file, item)

    if cutoff == len(results)-1:
        return None

    for result_file, _ in results[cutoff+1:]:
        with open(result_file, 'r') as ifp:
            crawl_result = json.load(ifp)
        for item in crawl_result.get('data', []):
            yield parse_repository_metadata(result_file, item)

def sync(
        conn: sqlite3.Connection,
        results: Iterator[Tuple[Dict[str, Any], Optional[SyncParseError]]],
        batch_size: int
    ) -> int:
    """
    Synchronizes a list of results from a github crawl into the SQLite database represented by the
    given connection.

    Args:
    conn
        Open connection to SQLite database
    results
        List of paths to crawl result files from which to sync to the database

    Returns: None
    """
    c = conn.cursor()

    insertion = """
    INSERT INTO repositories(github_id, full_name, owner, html_url, api_url, is_fork)
    VALUES (?, ?, ?, ?, ?, ?)
    """

    update_history = 'INSERT INTO history(github_id, synced_at) VALUES (?, ?)'

    synced = 0
    batch = []
    github_id = -1
    for item, err in tqdm(results):
        if err is not None:
            print('Parse error - {}'.format(repr(err)), file=sys.stderr)
            continue

        parsed_item = (
            item['id'],
            item['full_name'],
            item['owner_login'],
            item['html_url'],
            item['url'],
            item['fork'],
        )
        batch.append(parsed_item)
        github_id = item['id']

        if len(batch) % batch_size == 0:
            c.executemany(insertion, batch)
            c.execute(update_history, (github_id, datetime.now(tz=timezone.utc)))
            conn.commit()
            batch = []
            synced += batch_size

    if batch:
        c.executemany(insertion, batch)
        c.execute(update_history, (github_id, datetime.now(tz=timezone.utc)))
        conn.commit()
        synced += len(batch)

    return synced


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('--setup', help='If set, creates the relevant tables in the given database')
@click.option('--crawldir', '-d', help='Path to directory containing results of a GitHub crawl')
@click.option('--batch-size', '-b', type=int, default=1000, help='Number of repositories to sync at a time (database transaction batching)')
@click.option('--database', '-o', help='Path to database file')
def handler(setup: str, crawldir: str, batch_size: int, database: str) -> None:
    """
    CLI handler for sync functionality

    Args:
    args
        Argparse namespace containing parsed command line arguments

    Returns: None
    """
    conn = sqlite3.connect(database)
    try:
        if setup:
            setup_database(conn)

        results = ordered_crawl(crawldir)
        tasks = unsynced_results(conn, results)
        print(sync(conn, tasks, batch_size))
    finally:
        conn.close()