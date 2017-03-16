import hashlib
from datetime import datetime

from .items import CDRItem, CDRMediaItem


def text_cdr_item(response, *, crawler_name, team_name,
                  objects=None, metadata=None, item_cls=CDRItem):
    content_type = response.headers.get('content-type', b'')
    return cdr_item(
        response.url,
        crawler_name=crawler_name,
        team_name=team_name,
        content_type=content_type.decode('ascii', 'ignore'),
        raw_content=response.text,
        item_cls=item_cls,
        objects=objects or [],
        metadata=metadata or {},
    )


def cdr_item(url, *, crawler_name, team_name, item_cls=CDRItem, **extra):
    timestamp_crawl = format_timestamp(datetime.utcnow())
    return item_cls(
        _id=format_id(url, timestamp_crawl),
        crawler=crawler_name,
        team=team_name,
        timestamp_crawl=timestamp_crawl,
        url=url,
        version=3.0,
        **extra)


def media_cdr_item(url, *, stored_url, content_type, timestamp_crawl=None):
    return CDRMediaItem(
        obj_original_url=url,
        obj_stored_url=stored_url,
        content_type=content_type,
        timestamp_crawl=timestamp_crawl or format_timestamp(datetime.utcnow()),
    )


def format_timestamp(dt):
    return '{}Z'.format(dt.isoformat())


def format_id(url, timestamp_crawl):
    return (hashlib.sha256('{}-{}'.format(url, timestamp_crawl).encode('utf-8'))
            .hexdigest().upper())
