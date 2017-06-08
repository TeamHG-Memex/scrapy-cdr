Changes
=======

.. contents::

0.3.1 (2017-06-08)
------------------

- Support CDR v3.1 format (add ``response_headers``)


0.3.0 (2017-04-07)
------------------

- Add ``cdr-es-download`` script to download data from CDR
- ``CDRMediaPipeline``: use "https://" URL for public media items on S3


0.2.1 (2017-04-05)
------------------

- ``cdr-es-upload``: log exceptions when reading data to upload


0.2.0 (2017-03-17)
------------------

- Updated to CDR v3 (breaking change)
- Added ``cdr-v2-to-v3`` script for CDR v2 -> v3 conversion
- Added ``cdr-es-upload`` script for Elasticsearch upload
- Added ``scrapy_cdr.media_pipeline.CDRMediaPipeline`` to help with
  media item downloading


0.1.2 (2017-02-02)
------------------

- Do not fail on responses without content-type header


0.1.1 (2016-08-10)
------------------

- Allow passing a custom item class


0.1.0 (2016-06-18)
------------------

Initial release
