Scrapy CDR
==========

Item definition and utils for storing items in CDR format for scrapy.

Install
-------

::

    pip install scrapy-cdr


Usage
-----

::

    from scrapy_cdr import text_cdr_item

    def parse(response):
        yield text_cdr_item(
            response,
            crawler_name='my scrapy crawler',
            team_name='my team',
            metadata={'extra': 'metadata'},  # optional
            )

There is also ``scrapy_cdr.cdr_item`` for non-text items,
and item definition in ``scrapy_cdr.CDRItem``.


License
-------

License is MIT.
