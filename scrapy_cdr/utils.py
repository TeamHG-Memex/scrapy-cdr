import hashlib
from datetime import datetime

from .items import CDRItem


def text_cdr_item(response, *, crawler_name, team_name, metadata=None, item_cls=CDRItem):
    return cdr_item(
        response.url,
        metadata=metadata,
        crawler_name=crawler_name,
        team_name=team_name,
        content_type=response.headers['content-type']
            .decode('ascii', 'ignore'),
        extracted_text=extract_text(response),
        raw_content=response.text,
        item_cls=item_cls,
    )


def cdr_item(url, *, crawler_name, team_name, metadata=None, item_cls=CDRItem, **extra):
    metadata = metadata or {}
    timestamp = int(datetime.utcnow().timestamp() * 1000)
    return item_cls(
        _id=hashlib.sha256('{}-{}'.format(url, timestamp).encode('utf-8'))
            .hexdigest().upper(),
        crawler=crawler_name,
        extracted_metadata=metadata,
        team=team_name,
        timestamp=timestamp,
        url=url,
        version=2.0,
        **extra)


def extract_text(response):
    return '\n'.join(response.xpath('//body').xpath('string()').extract())
