from __future__ import absolute_import

import pytest
import scrapy
from scrapy.crawler import CrawlerRunner
from scrapy.linkextractors import LinkExtractor
from scrapy.settings import Settings
from twisted.web.resource import Resource

from scrapy_cdr import text_cdr_item
from .mockserver import MockServer
from .utils import text_resource, find_item, inlineCallbacks


class Spider(scrapy.Spider):
    name = 'test_spider'

    def __init__(self, url):
        super(Spider, self).__init__()
        self.start_urls = [url]
        self.le = LinkExtractor(canonicalize=False)
        self.files_le = LinkExtractor(
            tags=['a'], attrs=['href'], deny_extensions=[], canonicalize=False)

    def parse(self, response):
        follow_urls = [link.url for link in self.le.extract_links(response)]
        file_urls = (
            {link.url for link in self.files_le.extract_links(response)} -
            set(follow_urls))
        yield text_cdr_item(
            response,
            objects=file_urls,
            crawler_name='test', team_name='scrapy-cdr')
        for url in follow_urls:
            yield scrapy.Request(url)


def make_crawler(**extra_settings):
    settings = Settings()
    settings['ITEM_PIPELINES'] = {
        'scrapy_cdr.media_pipeline.CDRMediaPipeline': 1,
        'tests.utils.CollectorPipeline': 100,
    }
    settings.update(extra_settings)
    runner = CrawlerRunner(settings)
    return runner.create_crawler(Spider)


FILE_CONTENTS = b'\x98\x11Pr\xe7\x17\x8f'


class PDFFile(Resource):
    isLeaf = True

    def render_GET(self, request):
        request.setHeader(b'content-type', b'application/pdf')
        request.setHeader(b'content-hype', b'very/high')
        return FILE_CONTENTS


class WithFile(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.putChild(b'', text_resource(
            '<a href="/file.pdf">file</a> '
            '<a href="/page?b=2&a=1">page</a> '
            '<a href="/another-page">another page</a> '
            '<a href="/forbidden.pdf">forbidden file</a>'
        )())
        self.putChild(b'file.pdf', PDFFile())
        self.putChild(b'forbidden.pdf', text_resource(FILE_CONTENTS * 2)())
        self.putChild(b'page', text_resource(
            '<a href="/file.pdf?allow=true">file</a>')())
        self.putChild(b'another-page', text_resource(
            '<a href="/file.pdf">file</a>')())


@inlineCallbacks
@pytest.mark.parametrize(['max_cache'], [[1], [10000], [None]])
def test_media_pipeline(tmpdir, max_cache):
    crawler = make_crawler(FILES_STORE='file://{}'.format(tmpdir),
                           FILES_MAX_CACHE=max_cache)
    with MockServer(WithFile) as s:
        root_url = s.root_url
        yield crawler.crawl(url=root_url)
    spider = crawler.spider
    assert len(spider.collected_items) == 3

    root_item = find_item('/', spider.collected_items)
    assert len(root_item['objects']) == 2
    file_item = find_item(
        '/file.pdf', root_item['objects'], 'obj_original_url')
    assert file_item['obj_original_url'] == root_url + '/file.pdf'
    assert not file_item['obj_stored_url'].endswith('.pdf')
    with tmpdir.join(file_item['obj_stored_url']).open('rb') as f:
        assert f.read() == FILE_CONTENTS
    assert file_item['content_type'] == 'application/pdf'
    headers = dict(file_item['response_headers'])
    headers.pop('date')
    headers.pop('server')
    assert headers == {'content-type': 'application/pdf',
                       'content-hype': 'very/high'}

    forbidden_item = find_item(
        '/forbidden.pdf', root_item['objects'], 'obj_original_url')
    with tmpdir.join(forbidden_item['obj_stored_url']).open('rb') as f:
        assert f.read() == FILE_CONTENTS * 2

    page_item = find_item('/page?b=2&a=1', spider.collected_items)
    file_item_q = find_item(
        '/file.pdf?allow=true', page_item['objects'], 'obj_original_url')
    assert file_item_q['obj_stored_url'] == file_item['obj_stored_url']

    another_page_item = find_item('/another-page', spider.collected_items)
    file_item_q = find_item(
        '/file.pdf', another_page_item['objects'], 'obj_original_url')
    assert file_item_q['obj_stored_url'] == file_item['obj_stored_url']
    assert file_item_q['obj_original_url'] == file_item['obj_original_url']
