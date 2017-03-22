#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

__version__ = '0.0.3'

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist bdist_wheel upload')
    os.system("git tag -a {0} -m 'version {0}'".format(__version__))
    os.system("git push --tags")
    sys.exit()

setup(
    name='leankit',
    packages=['leankit'],
    version=__version__,
    description='Simple wrapper for the Leankit API',
    author='Guillermo Guirao Aguilar',
    author_email='contact@guillermoguiraoaguilar.com',
    url='https://github.com/Funk66/leankit.git',
    keywords=['leankit'],
    install_requires=['requests', 'cached_property', 'pyyaml', 'pytz'],
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
