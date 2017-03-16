from datetime import datetime
import hashlib
import logging
import os.path

from scrapy import Request
from scrapy.pipelines.files import FilesPipeline, S3FilesStore
from .utils import format_timestamp, media_cdr_item


logging.getLogger('botocore').setLevel(logging.WARNING)


class CDRMediaPipeline(FilesPipeline):
    """ A pipeline that downloads media items and puts them into "objects"
    field of the CDR item according to CDR v3 schema.

    Usage:

    1. Optionally, subclass and re-defined media_request method if you want to
       customize how media items are downloaded.
    2. Add the pipeline to ITEM_PIPELINES in settings::

        ITEM_PIPELINES = {
            'undercrawler.media_pipeline.UndercrawlerMediaPipeline': 1,
        }

    3. Set ``FILES_STORE`` as you would do for scrapy FilesPipeline.
    4. Put urls to download into "objects" field of the cdr item in the crawler,
       for example::

        yield scrapy_cdr.utils.text_cdr_item(
            response,
            crawler_name='name',
            team_name='team',
            objects=['http://example.com/1.png', 'http://example.com/1.png'],
        )
    """

    def media_request(self, url):
        # Override to provide your own downloading logic
        return Request(url)

    def get_media_requests(self, item, info):
        return [self.media_request(url) for url in item.get('objects', [])]

    def media_to_download(self, request, info):
        # downloaded items have already been filtered as duplicate
        return None

    def item_completed(self, results, item, info):
        item['objects'] = []
        for res in (x for ok, x in results if ok):
            path = res['path']
            if isinstance(self.store, S3FilesStore):
                path = 's3://{}/{}{}'.format(
                    self.store.bucket, self.store.prefix, path)
            item['objects'].append(media_cdr_item(
                res['url'],
                stored_url=path,
                content_type=res['content_type'],
                timestamp_crawl=res['timestamp_crawl'],
            ))
        return item

    def file_path(self, request, response=None, info=None):
        assert response is not None
        name = hashlib.sha256(response.body).hexdigest().upper()
        media_ext = os.path.splitext(request.url)[1]
        return '{}{}'.format(name, media_ext)

    def media_downloaded(self, response, request, info):
        result = super().media_downloaded(response, request, info)
        result.pop('checksum', None)
        result['content_type'] = response.headers.get(b'content-type', b'') \
            .decode('ascii', 'ignore')
        result['timestamp_crawl'] = format_timestamp(datetime.utcnow())
        return result
