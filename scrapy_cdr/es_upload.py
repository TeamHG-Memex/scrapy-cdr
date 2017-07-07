import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from itertools import islice
import logging
import os
import shutil
import sys
from six.moves.urllib.parse import urlsplit
import time
import traceback

import json_lines
import elasticsearch
import elasticsearch.helpers as es_helpers

from .utils import format_timestamp


def main():
    parser = argparse.ArgumentParser(description='Upload items to ES index')
    arg = parser.add_argument
    arg('inputs', nargs='+', help='inputs in .jl or .jl.gz format')
    arg('index', help='ES index name')
    arg('--type', default='document',
        help='ES type to use ("document" by default)')
    arg('--op-type', default='index',
        choices={'index', 'create', 'delete', 'update'},
        help='ES operation type to use ("index" by default)')
    arg('--broken', action='store_true',
        help='specify if input might be broken (incomplete)')
    arg('--host', default='localhost', help='ES host in host[:port] format')
    arg('--user', help='HTTP Basic Auth user')
    arg('--password', help='HTTP Basic Auth password')
    arg('--chunk-size', type=int, default=50, help='upload chunk size')
    arg('--threads', type=int, default=4, help='number of threads')
    arg('--limit', type=int, help='Index first N items')
    arg('--format', choices=['CDRv2', 'CDRv3'], default='CDRv3')
    arg('--max-chunk-bytes', type=int, default=10 * 2**20,
        help='Depends on how ES is configured. 10 MB on AWS (default).')
    arg('--log-level', default='INFO')
    arg('--log-file')
    arg('--reverse-domain-storage', action='store_true',
        help='Store objects in reverse domain folder structure. Objects '
             'will be copied in the filesystem. --media-root must be set.')
    arg('--media-root', help='path to the root of stored media objects')

    args = parser.parse_args()
    if args.reverse_domain_storage and not args.media_root:
        parser.error('--media-root must be set with --reverse-domain-objects')

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s [%(levelname)s] %(module)s: %(message)s',
        filename=args.log_file)
    logging.getLogger('elasticsearch').setLevel(logging.WARNING)

    kwargs = {}
    if args.user or args.password:
        kwargs['http_auth'] = (args.user, args.password)

    client = elasticsearch.Elasticsearch(
        [args.host],
        connection_class=elasticsearch.RequestsHttpConnection,
        timeout=600,
        **kwargs)
    logging.info(client.info())

    def _items():
        for filename in args.inputs:
            logging.info('Starting {}'.format(filename))
            with json_lines.open(filename, broken=args.broken) as f:
                for item in f:
                    yield item

    is_cdrv3 = args.format == 'CDRv3'

    def _actions():
        items = _items()
        if args.limit:
            items = islice(items, args.limit)
        for item in items:

            if is_cdrv3:
                assert 'timestamp_crawl' in item, \
                       'this is not CDRv3, check --format'
            else:
                assert 'timestamp' in item, 'this is not CDRv2, check --format'

            if is_cdrv3:
                item['timestamp_index'] = format_timestamp(datetime.utcnow())
            elif isinstance(item['timestamp'], int):
                item['timestamp'] = format_timestamp(
                    datetime.fromtimestamp(item['timestamp'] / 1000.))

            if args.reverse_domain_storage:
                _reverse_domain_storage(item, args.media_root)

            action = {
                '_op_type': args.op_type,
                '_index': args.index,
                '_type': args.type,
                '_id': item.pop('_id'),
            }
            if is_cdrv3:
                item.pop('metadata', None)  # not in CDRv3 schema
            else:
                item.pop('extracted_metadata', None)
            if args.op_type != 'delete':
                action['_source'] = item
            yield action

    # This wrapper is needed due to use of raise_on_error=False
    # below (which we need because ES can raise exceptions on timeouts, etc.),
    # but we don't want to ignore errors when reading data.
    failed = [False]  # to set correct exit code

    def actions():
        try:
            for x in _actions():
                yield x
        except Exception:
            traceback.print_exc()
            failed[0] = True
            raise  # will be caught anyway

    t0 = t00 = time.time()
    i = last_i = 0
    result_counts = defaultdict(int)
    try:
        for i, (success, result) in enumerate(
                parallel_bulk(
                    client,
                    actions=actions(),
                    thread_count=args.threads,
                    chunk_size=args.chunk_size,
                    raise_on_error=False,
                    raise_on_exception=False,
                    max_chunk_bytes=args.max_chunk_bytes,
                ), start=1):
            op_result = result[args.op_type].get('result')
            if op_result is None:
                # ES 2.x
                op_result = ('status_{}'
                             .format(result[args.op_type].get('status')))
            result_counts[op_result] += 1
            if not (success or (args.op_type == 'delete' and
                                op_result in {'not_found', 'status_404'})):
                logging.info('ES error: {}'.format(str(result)[:2000]))
                failed[0] = True
            t1 = time.time()
            if t1 - t0 > 10:
                _report_stats(i, last_i, t1 - t0, result_counts)
                t0 = t1
                last_i = i
    finally:
        _report_stats(i, 0, time.time() - t00, result_counts)

    if failed[0]:
        sys.exit(1)


def _reverse_domain_storage(item, media_root):
    for obj in item.get('objects', []):
        stored_url = obj['obj_stored_url']
        assert '/' not in stored_url
        domain = urlsplit(obj['obj_original_url']).netloc
        if ':' in domain:
            domain, _ = domain.split(':', 1)
        parents = [p for p in reversed(domain.split('.')) if p]
        os.makedirs(os.path.join(media_root, *parents), exist_ok=True)
        stored_url_noext, _ = os.path.splitext(stored_url)
        new_stored_url = os.path.sep.join(parents + [stored_url_noext])
        dest = os.path.join(media_root, new_stored_url)
        if not os.path.exists(dest):
            shutil.copy(os.path.join(media_root, stored_url), dest)
        obj['obj_stored_url'] = new_stored_url


def _report_stats(items, prev_items, dt, result_counts):
    logging.info(
        '{items:,} items processed ({stats}) at {speed:.0f} items/s'
        .format(items=items,
                stats=', '.join(
                    '{}: {:,}'.format(k, v)
                    for k, v in sorted(result_counts.items()) if v != 0),
                speed=(items - prev_items) / dt,
                )
    )


def parallel_bulk(client, actions, thread_count=4, chunk_size=500,
                  max_chunk_bytes=100 * 1024 * 1024,
                  expand_action_callback=es_helpers.expand_action,
                  **kwargs):
    """ es_helpers.parallel_bulk rewritten with imap_fixed_output_buffer
    instead of Pool.imap, which consumed unbounded memory if the generator
    outruns the upload (which usually happens).
    """
    actions = map(expand_action_callback, actions)
    for result in imap_fixed_output_buffer(
            lambda chunk: list(
                es_helpers._process_bulk_chunk(client, chunk, **kwargs)),
            es_helpers._chunk_actions(actions, chunk_size, max_chunk_bytes,
                                      client.transport.serializer),
            threads=thread_count,
        ):
        for item in result:
            yield item


def imap_fixed_output_buffer(fn, it, threads: int):
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = []
        max_futures = threads + 1
        for i, x in enumerate(it):
            while len(futures) >= max_futures:
                future, futures = futures[0], futures[1:]
                yield future.result()
            futures.append(executor.submit(fn, x))
        for future in futures:
            yield future.result()
