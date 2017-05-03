import argparse
from collections import defaultdict
from datetime import datetime
from itertools import islice
import sys
import time
import traceback

import json_lines
import elasticsearch
import elasticsearch.helpers

from .utils import format_timestamp


def main():
    parser = argparse.ArgumentParser(description='Upload items to ES index')
    arg = parser.add_argument
    arg('input', help='input in .jl or .jl.gz format')
    arg('index', help='ES index name')
    arg('--type', default='document',
        help='ES type to use ("document" by default)')
    arg('--op-type', default='index',
        choices={'index', 'create', 'delete', 'update'},
        help='ES operation type to use ("document" by default)')
    arg('--broken', action='store_true',
        help='specify if input might be broken (incomplete)')
    arg('--host', default='localhost', help='ES host in host[:port] format')
    arg('--user', help='HTTP Basic Auth user')
    arg('--password', help='HTTP Basic Auth password')
    arg('--chunk-size', type=int, default=50, help='upload chunk size')
    arg('--threads', type=int, default=8, help='number of threads')
    arg('--limit', type=int, help='Index first N items')
    arg('--format', choices=['CDRv2', 'CDRv3'], default='CDRv3')

    args = parser.parse_args()
    kwargs = {}
    if args.user or args.password:
        kwargs['http_auth'] = (args.user, args.password)

    client = elasticsearch.Elasticsearch(
        [args.host],
        connection_class=elasticsearch.RequestsHttpConnection,
        timeout=600,
        **kwargs)
    print(client.info())

    is_cdrv3 = args.format == 'CDRv3'

    def _actions():
        with json_lines.open(args.input, broken=args.broken) as f:
            items = islice(f, args.limit) if args.limit else f
            for item in items:

                if is_cdrv3:
                    assert 'timestamp_crawl' in item, 'this is not CDRv3, check --format'
                else:
                    assert 'timestamp' in item, 'this is not CDRv2, check --format'

                if is_cdrv3:
                    item['timestamp_index'] = format_timestamp(datetime.utcnow())
                elif isinstance(item['timestamp'], int):
                    item['timestamp'] = format_timestamp(
                        datetime.fromtimestamp(item['timestamp'] / 1000.))

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
    # below (which we need because es can raise exceptions on timeouts, etc.),
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
                elasticsearch.helpers.parallel_bulk(
                    client,
                    actions=actions(),
                    chunk_size=args.chunk_size,
                    thread_count=args.threads,
                    raise_on_error=False,
                ), start=1):
            op_result = result[args.op_type].get('result')
            if op_result is None:
                # ES 2.x
                op_result = 'status_{}'.format(result[args.op_type].get('status'))
            result_counts[op_result] += 1
            if args.op_type == 'delete':
                if not success:
                    assert op_result in {'not_found', 'status_404'}, result
            else:
                assert success, (success, op_result, result)
            t1 = time.time()
            if t1 - t0 > 10:
                _report_stats(i, last_i, t1 - t0, result_counts)
                t0 = t1
                last_i = i
    finally:
        _report_stats(i, 0, time.time() - t00, result_counts)

    if failed[0]:
        sys.exit(1)


def _report_stats(items, prev_items, dt, result_counts):
    print('{items:,} items processed ({stats}) at {speed:.0f} items/s'
          .format(
            items=items,
            stats=', '.join(
                '{}: {:,}'.format(k, v)
                for k, v in sorted(result_counts.items()) if v != 0),
            speed=(items - prev_items) / dt,
    ))
