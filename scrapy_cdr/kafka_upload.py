import argparse
from datetime import datetime
import json
from itertools import islice
import logging
from pathlib import Path
import time

import json_lines
from kafka import KafkaProducer

from .utils import format_timestamp


def main():
    parser = argparse.ArgumentParser(description='Upload items to ES index')
    arg = parser.add_argument
    arg('inputs', nargs='+', help='inputs in .jl or .jl.gz format')
    arg('topic', help='inputs in .jl or .jl.gz format')
    arg('--brokers', help='brokers (comma-separated), including port')
    arg('--limit', type=int, help='Index first N items')
    arg('--broken', action='store_true',
        help='specify if input might be broken (incomplete)')
    arg('--ssl-keys-path',
        help='path to ca-cert.pem, client-cert.pem and client-key.pem location')
    arg('--log-level', default='INFO')
    arg('--log-file')
    arg('--batch-size', type=int, default=32)
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s [%(levelname)s] %(module)s: %(message)s',
        filename=args.log_file)

    def _items():
        for filename in args.inputs:
            logging.info('Starting {}'.format(filename))
            with json_lines.open(filename, broken=args.broken) as f:
                for item in f:
                    yield item

    kafka_kwargs = dict(
        max_request_size=10 * 2**20,
        request_timeout_ms=120000,
        retries=5,
        retry_backoff_ms=30000,
        compression_type='gzip',
        batch_size=args.batch_size,  # but data is also flushed (see below)
    )
    if args.brokers:
        kafka_kwargs['bootstrap_servers'] = args.brokers.split(',')
    if args.ssl_keys_path:
        keys_path = Path(args.ssl_keys_path)
        kafka_kwargs.update(dict(
            security_protocol='SSL',
            ssl_check_hostname=False,
            ssl_cafile=str(keys_path / 'ca-cert.pem'),
            ssl_certfile=str(keys_path / 'client-cert.pem'),
            ssl_keyfile=str(keys_path / 'client-key.pem'),
        ))
    producer = KafkaProducer(**kafka_kwargs)

    items = _items()
    if args.limit:
        items = islice(items, args.limit)

    t0 = t00 = time.time()
    n_items = prev_n_items = 0
    try:
        for item in items:
            item['timestamp_index'] = format_timestamp(datetime.utcnow())
            message = json.dumps(item).encode('utf8')
            producer.send(args.topic, message)
            n_items += 1
            if n_items % args.batch_size == 0:
                producer.flush()
            t1 = time.time()
            if t1 - t0 > 10:
                _report_stats(n_items, prev_n_items, t1 - t0)
                t0 = t1
                prev_n_items = n_items
    finally:
        _report_stats(n_items, 0, time.time() - t00)
        producer.flush()


def _report_stats(n_items, prev_n_items, dt):
    logging.info('{n_items:,} items processed at {speed:.0f} items/s'
                 .format(n_items=n_items, speed=(n_items - prev_n_items) / dt))
