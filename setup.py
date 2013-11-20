#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from octopus import __version__

tests_require = [
    'mock',
    'nose',
    'coverage',
    'yanc',
    'preggy',
    'tox',
    'ipdb',
    'coveralls',
]

setup(
    name='octopus-http',
    version=__version__,
    description='Octopus is a library to use threads to concurrently retrieve and report on the completion of http requests',
    long_description='''
Octopus is a library to use threads to concurrently retrieve and report on the completion of http requests
''',
    keywords='http concurrency threading',
    author='Bernardo Heynemann',
    author_email='heynemann@gmail.com',
    url='https://heynemann.github.io/octopus',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: MacOS',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
    ],
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'six',
        'requests',
        'tornado'
    ],
    extras_require={
        'tests': tests_require,
    },
)
