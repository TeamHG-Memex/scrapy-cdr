import scrapy


class CDRItem(scrapy.Item):

    # (url)-(crawl timestamp), SHA-256 hashed, UPPERCASE (string)
    _id = scrapy.Field()

    # MIME type (multi (strings))
    content_type = scrapy.Field()

    # Text label identifying the software used by the crawler (string)
    crawler = scrapy.Field()

    # Tika/other extraction output (object)
    extracted_metadata = scrapy.Field()

    # Tika/other extraction output (string)
    extracted_text = scrapy.Field()

    # If present, this will contain the _id field of a parent record (string)
    obj_parent = scrapy.Field()

    # URL reference to a binary object's original location (string)
    obj_original_url = scrapy.Field()

    # URL reference to a cached copy of a binary object,
    # suggested format to minimize duplication:
    # filename is the UPPERCASE hash SHA-256 of the object
    obj_stored_url = scrapy.Field()

    # Original source text/html (string)
    raw_content = scrapy.Field()

    # Text label identifying the team responsible for the crawler (string)
    team = scrapy.Field()

    # Timestamp of COLLECTION of data from the web (datetime)
    # https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping-date-format.html#built-in-date-formats
    timestamp = scrapy.Field()

    # Full URL requested by the crawler (multi (strings))
    url = scrapy.Field()

    # Schema version. This document describes schema version 2.0. (float)
    version = scrapy.Field()

    def __repr__(self):
        fields = ['_id', 'url', 'timestamp', 'extracted_metadata']
        return '<CDRItem: {}>'.format(', '.join(
            '{}: {}'.format(f, repr(self[f])) for f in fields))
