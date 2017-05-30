#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


__version__ = '1.2.0'


setup(
    name='leankit',
    packages=['leankit'],
    version=__version__,
    description='Simple wrapper for the Leankit API',
    author='Guillermo Guirao Aguilar',
    author_email='contact@guillermoguiraoaguilar.com',
    url='https://github.com/Funk66/leankit.git',
    keywords=['leankit'],
    install_requires=['dateutils', 'requests', 'cached_property', 'pytz'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Utilities'
    ]
)
