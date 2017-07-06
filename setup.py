#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import path
from setuptools import setup


def version():
    init = path.join(path.dirname(__file__), 'leankit', '__init__.py')
    line = list(filter(lambda l: l.startswith('__version__'), open(init)))[0]
    return line.split('=')[-1].strip(" '\"\n")


setup(name='leankit',
      packages=['leankit'],
      version=version(),
      author='Guillermo Guirao Aguilar',
      author_email='contact@guillermoguiraoaguilar.com',
      url='https://github.com/Funk66/leankit',
      install_requires=['dateutils', 'cached_property', 'requests', 'pytz'],
      setup_requires=['nose', 'rednose', 'coverage'],
      classifiers=['Programming Language :: Python :: 3.5'])
