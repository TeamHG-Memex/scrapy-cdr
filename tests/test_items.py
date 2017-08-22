from datetime import datetime

from scrapy.http.headers import Headers
from scrapy.http.response.text import TextResponse

from scrapy_cdr.utils import text_cdr_item, media_cdr_item


def test_text_cdr_item():
    response = TextResponse(
        url='http://example.com',
        headers={'Content-Type': 'text/plain',
                 'another-header': 'text/complain, text/explain'},
        body=b'a body',
        encoding='utf8')
    item = text_cdr_item(response, crawler_name='crawler', team_name='team')
    item = dict(item)
    item_id = item.pop('_id')  # type: str
    assert item_id.isupper()
    check_timestamp_crawl(item)
    assert dict(item) == {
        'content_type': 'text/plain',
        'crawler': 'crawler',
        'objects': [],
        'raw_content': 'a body',
        'response_headers': {'content-type': 'text/plain',
                             'another-header': 'text/complain, text/explain'},
        'team': 'team',
        'url': 'http://example.com',
        'version': 3.1}


def check_timestamp_crawl(item):
    timestamp_crawl = item.pop('timestamp_crawl')
    datetime.strptime(timestamp_crawl, '%Y-%m-%dT%H:%M:%S.%fZ')


def test_media_cdr_item():
    item = dict(media_cdr_item(
        url='http://example.com/1.png',
        stored_url='1.png',
        headers=Headers({'Content-Type': 'image/png',
                         'another-header': 'another_value'}),
    ))
    check_timestamp_crawl(item)
    assert item == {
        'obj_original_url': 'http://example.com/1.png',
        'obj_stored_url': '1.png',
        'content_type': 'image/png',
        'response_headers': {'content-type': 'image/png',
                             'another-header': 'another_value'},
    }
