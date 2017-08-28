from setuptools import setup


setup(
    name='scrapy-cdr',
    version='0.5.1',
    packages=['scrapy_cdr'],
    install_requires=[
        'botocore',
        'cachetools',
        'json_lines',
        'requests',
        'scrapy',
        'six',
        'tqdm',
    ],
    extras_requires={
        'es': [
            'elasticsearch',
            'elasticsearch-dsl',
        ],
        ':python_version<"3.0"': ['futures'],
    },
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
        'Programming Language :: Python :: 3.6',
    ],
)
