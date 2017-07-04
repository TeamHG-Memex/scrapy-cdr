Changes
=======

.. contents::

0.3.4 (2017-07-04)
------------------

- ``cdr-es-upload`` fixes: run in constant memory, proceed after ES upload
  errors (e.g. exceeding upload size).


0.3.3 (2017-07-04)
------------------

- ``cdr-es-upload`` fixes: add ``--max-chunk-bytes`` and set it to 10 MB
  by default (was 100 MB before), proceed after indexing errors.


0.3.2 (2017-06-14)
------------------

- Fix file extension handling in ``CDRMediaPipeline``: now only url path
  is used (without query and fragment).


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
