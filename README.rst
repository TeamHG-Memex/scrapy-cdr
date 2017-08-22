Scrapy CDR
==========

.. image:: https://img.shields.io/pypi/v/scrapy-cdr.svg
   :target: https://pypi.python.org/pypi/scrapy-cdr
   :alt: PyPI Version

.. image:: https://travis-ci.org/TeamHG-Memex/scrapy-cdr.svg?branch=master
   :target: http://travis-ci.org/TeamHG-Memex/scrapy-cdr
   :alt: Build Status

.. image:: http://codecov.io/github/TeamHG-Memex/scrapy-cdr/coverage.svg?branch=master
   :target: http://codecov.io/github/TeamHG-Memex/scrapy-cdr?branch=master
   :alt: Code Coverage

Item definition, various utils and helpers for working with CDR format for scrapy.
Main supported format is CDR v3.1, but there is CDR v2 support for uploading to ES
and a v2 -> v3 converter. If you need CDR v2 support, use ``scrapy-cdr==0.1.2``.

.. contents::

Install
-------

::

    pip install scrapy-cdr


Usage
-----

Items
+++++

::

    from scrapy_cdr import text_cdr_item

    def parse(response):
        yield text_cdr_item(
            response,
            crawler_name='my scrapy crawler',
            team_name='my team',
            item_cls=MyCDRItem,  # optional
            )

There is also ``scrapy_cdr.cdr_item`` for non-text items,
and an item definition in ``scrapy_cdr.CDRItem``.


Media items
+++++++++++

``scrapy_cdr.media_pipeline.CDRMediaPipeline`` helps to download items
and puts them into "objects" field of the CDR item according to CDR v3 schema.

1. Add the pipeline to ``ITEM_PIPELINES`` in ``settings.py``::

    ITEM_PIPELINES = {
        'scrapy_cdr.media_pipeline.CDRMediaPipeline': 1,
    }

   Also you probably want to allow redirects in the media pipeline::

    MEDIA_ALLOW_REDIRECTS = True

2. Set ``FILES_STORE`` as you would do for scrapy FilesPipeline.
3. Put urls to download into "objects" field of the cdr item in the crawler,
   for example::

    yield scrapy_cdr.utils.text_cdr_item(
        response,
        crawler_name='name',
        team_name='team',
        objects=['http://example.com/1.png', 'http://example.com/1.png'],
    )

4. Optionally, customize ``CDRMediaPipeline``:

   - ``FILES_MAX_CACHE`` set maximum size of the downloader cache, and is
     10000 by default (unlike unbounded cache used in scrapy).

   - Set ``CDR_S3_RELATIVE_URLS = False`` option to use
     absolute URLs in ``objects`` array (``obj_stored_url``) when data is
     stored to S3. By default, S3 URLs are relative, i.e. they don't
     contain path and bucket. Local paths are always relative, regardless
     of this option.

5. Optionally, subclass the ``CDRMediaPipeline`` and re-define some methods:

   - ``media_request`` method if you want to
     customize how media items are downloaded.
   - ``s3_path`` method if you are storing media items in S3
     (``FILES_STORE`` is "s3://...") and want to customize the S3 URL of
     stored items. When URLs are absolute (``CDR_S3_RELATIVE_URLS = False``),
     by default it is "https://" urls for public items
     (if ``FILES_STORE_S3_ACL`` is ``public-read`` or ``public-read-write``),
     and "s3://" for private items (default in scrapy).


Uploading to Elasticsearch
++++++++++++++++++++++++++

``cdr-es-upload`` script takes care of generating
``timestamp_index`` field and can be used for uploading or deletion of
CDR items. Please see ``cdr-es-upload --help`` for help on command line options.


Converting from CDR v2 format
+++++++++++++++++++++++++++++

Use ``cdr-v2-to-v3`` script::

    cdr-v2-to-v3 items.v2.jl.gz items.v3.jl.gz --broken

Note that this script does not support media items.


License
-------

License is MIT.
