import argparse
import gzip
import json

import elasticsearch
from elasticsearch_dsl import Search
import tqdm


def main():
    parser = argparse.ArgumentParser(description='Download items from ES index')
    arg = parser.add_argument
    arg('output', help='output in .jl.gz format')
    arg('index', help='ES index name')
    arg('--domain', help='url.domain to filter')
    arg('--host', default='localhost', help='ES host in host[:port] format')
    arg('--user', help='HTTP Basic Auth user')
    arg('--password', help='HTTP Basic Auth password')
    arg('--chunk-size', type=int, default=100, help='download chunk size')

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

    search = Search(using=client, index=args.index)
    if args.domain:
        search = search.filter('term', **{'url.domain': args.domain})

    total = 0
    with tqdm.tqdm(total=search.count()) as pbar:
        with gzip.open(args.output, 'wt') as f:
            for x in search.params(size=args.chunk_size).scan():
                total += 1
                pbar.update(1)
                f.write(json.dumps(x.to_dict()))
                f.write('\n')

    print('{:,} items downloaded to {}'.format(total, args.output))
