import argparse
from datetime import datetime
import logging
import time

import json_lines
import elasticsearch
import elasticsearch.helpers

from .utils import format_timestamp


def main():
    # logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description='Upload items to ES index')
    arg = parser.add_argument
    arg('input', help='input in .jl or .jl.gz format')
    arg('index', help='ES index name')
    arg('--broken', action='store_true',
        help='specify if input might be broken (incomplete)')
    arg('--host', default='localhost', help='ES host in host[:port] format')
    arg('--user', help='HTTP Basic Auth user')
    arg('--password', help='HTTP Basic Auth password')
    arg('--chunk-size', type=int, default=50, help='upload chunk size')
    arg('--threads', type=int, default=8, help='number of threads')

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

    def items():
        with json_lines.open(args.input, broken=args.broken) as f:
            from itertools import islice
            for item in f:
                item['timestamp_index'] = format_timestamp(datetime.utcnow())
                yield {
                    '_index': args.index,
                    '_type': 'document',
                    '_id': item.pop('_id'),
                    '_source': item,
                }

    t0 = time.time()
    last_i = 0
    updated = created = 0
    for i, (success, result) in enumerate(
            elasticsearch.helpers.parallel_bulk(
                client,
                actions=items(),
                chunk_size=args.chunk_size,
                thread_count=args.threads,
            ), start=1):
        assert success, (success, result)
        result_op = result['index']['result']
        if result_op == 'updated':
            updated += 1
        elif result_op == 'created':
            created += 1
        else:
            print('Unexpected result', result_op, result)
        t1 = time.time()
        if t1 - t0 > 30:
            print('{:,} items processed ({:,} created, {:,} updated) '
                  'at {:.0f} items/s'
                  .format(i, created, updated,
                          (i - last_i) / (t1 - t0),
                  ))
            t0 = t1
            last_i = i
