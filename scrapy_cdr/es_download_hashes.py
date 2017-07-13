import argparse
import csv
import hashlib

import elasticsearch
from elasticsearch_dsl import Search
import tqdm
from w3lib.url import canonicalize_url


def main():
    parser = argparse.ArgumentParser(
        description='Download item hashes from ES index')
    arg = parser.add_argument
    arg('output', help='output in .csv format')
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
        with open(args.output, 'wt') as f:
            writer = csv.writer(f)
            for x in search.params(size=args.chunk_size).scan():
                total += 1
                pbar.update(1)
                x = x.to_dict()
                writer.writerow([
                    x['timestamp_crawl'],
                    (hashlib.sha1((x['raw_content'] or '')
                     .encode('utf8')).hexdigest()),
                    x['team'],
                    x['url'],
                    canonicalize_url(x['url'], keep_fragments=True),
                ])

    print('{:,} items downloaded to {}'.format(total, args.output))


if __name__ == '__main__':
    main()
