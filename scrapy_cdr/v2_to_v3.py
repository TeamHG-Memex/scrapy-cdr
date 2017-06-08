import argparse
from datetime import datetime
try:
    import ujson as json
except ImportError:
    import json
import gzip

import json_lines

from .items import CDRItem
from .utils import format_timestamp, format_id


def main():
    parser = argparse.ArgumentParser()
    arg = parser.add_argument
    arg('input', help='.jl or .jl.gz file in CDRv2 format')
    arg('output', help='path to .jl or .jl.gz output in CDRv3 format')
    arg('--broken', action='store_true',
        help='specify if input might be broken (incomplete)')
    args = parser.parse_args()
    assert args.input != args.output

    with json_lines.open(args.input, broken=args.broken) as f:
        opener = gzip.open if args.output.endswith('.gz') else open
        with opener(args.output, 'wt') as outf:
            for v2_item in f:
                dt = datetime.fromtimestamp(v2_item['timestamp'] / 1e3)
                timestamp_crawl = format_timestamp(dt)
                assert v2_item['version'] == 2.0
                v3_item = CDRItem(
                    _id=format_id(v2_item['url'], timestamp_crawl),
                    crawler=v2_item['crawler'],
                    team=v2_item['team'],
                    timestamp_crawl=timestamp_crawl,
                    version=3.0,
                    url=v2_item['url'],
                    raw_content=v2_item['raw_content'],
                    content_type=v2_item['content_type'],
                    response_headers={'content-type': v2_item['content_type']},
                )
                outf.write(json.dumps(dict(v3_item)))
                outf.write('\n')
