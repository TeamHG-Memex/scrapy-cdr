from setuptools import setup


setup(
    name='scrapy-cdr',
    version='0.3.2',
    packages=['scrapy_cdr'],
    install_requires=[
        'botocore',
        'elasticsearch',
        'elasticsearch-dsl',
        'json_lines',
        'requests',
        'scrapy',
        'six',
        'tqdm',
    ],
    entry_points={
        'console_scripts': [
            'cdr-v2-to-v3=scrapy_cdr.v2_to_v3:main',
            'cdr-es-upload=scrapy_cdr.es_upload:main',
            'cdr-es-download=scrapy_cdr.es_download:main',
            ],
    },
    license='MIT license',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)
