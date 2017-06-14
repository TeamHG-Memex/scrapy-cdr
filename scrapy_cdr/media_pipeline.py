from datetime import datetime
import hashlib
import logging
import os.path
from six.moves.urllib.parse import urlsplit

from scrapy import Request
from scrapy.pipelines.files import FilesPipeline, S3FilesStore
from .utils import format_timestamp, media_cdr_item


logging.getLogger('botocore').setLevel(logging.WARNING)


class CDRMediaPipeline(FilesPipeline):
    """ A pipeline that downloads media items and puts them into "objects"
    field of the CDR item according to CDR v3 schema.

    Usage:

    1. Add the pipeline to ITEM_PIPELINES in settings::

        ITEM_PIPELINES = {
            'scrapy_cdr.media_pipeline.CDRMediaPipeline': 1,
        }

    2. Set ``FILES_STORE`` as you would do for scrapy FilesPipeline.
    3. Put urls to download into "objects" field of the cdr item in the crawler,
       for example::

        yield scrapy_cdr.utils.text_cdr_item(
            response,
            crawler_name='name',
            team_name='team',
            objects=['http://example.com/1.png', 'http://example.com/1.png'],
        )

    4. Optionally, subclass the ``CDRMediaPipeline`` and re-define some methods:

       - ``media_request`` method if you want to
         customize how media items are downloaded.
       - ``s3_path`` method if you are storing media items in S3
         (``FILES_STORE`` is "s3://...") and want to customize the S3 URL of
         stored items. By default it is "https://" urls for public items
         (if ``FILES_STORE_S3_ACL`` is ``public-read`` or ``public-read-write``),
         and "s3://" for private items (default in scrapy).
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
                path = self.s3_path(path)
            item['objects'].append(media_cdr_item(
                res['url'],
                stored_url=path,
                headers=res['headers'],
                timestamp_crawl=res['timestamp_crawl'],
            ))
        return item

    def s3_path(self, path):
        if self.store.POLICY in {'public-read', 'public-read-write'}:
            return 'https://{}.s3.amazonaws.com/{}{}'.format(
                self.store.bucket, self.store.prefix, path)
        else:
            return 's3://{}/{}{}'.format(
                self.store.bucket, self.store.prefix, path)

    def file_path(self, request, response=None, info=None):
        assert response is not None
        name = hashlib.sha256(response.body).hexdigest().upper()
        parsed = urlsplit(request.url)
        media_ext = os.path.splitext(parsed.path)[1]
        return '{}{}'.format(name, media_ext)

    def media_downloaded(self, response, request, info):
        result = super(CDRMediaPipeline, self)\
            .media_downloaded(response, request, info)
        result.pop('checksum', None)
        result['headers'] = response.headers
        result['timestamp_crawl'] = format_timestamp(datetime.utcnow())
        return result
