Scrapy CDR
==========

Item definition and utils for storing items in CDR v3 format for scrapy.


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

1. Optionally, subclass and re-defined ``media_request``
   method if you want to customize how media items are downloaded.
2. Add the pipeline to ``ITEM_PIPELINES`` in settings::

    ITEM_PIPELINES = {
        'scrapy_cdr.media_pipeline.CDRMediaPipeline': 1,
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


License
-------

License is MIT.
