#!/usr/bin/python
# -*- coding: utf-8 -*-

from logging import getLogger

log = getLogger(__name__)

from .connector import api
from .kanban import Board


__author__ = "Guillermo Guirao Aguilar"
__email__ = "contact@guillermoguiraoaguilar.com"
__license__ = "MIT"
__version__ = "1.2.0"


def get_boards():
    log.debug('Getting boards')
    return api.get('/Boards')


def get_newer_if_exists(board_id, version, timezone='UTC'):
    """ Downloads a board if a newer version number exists """
    url = '/Board/{}/BoardVersion/{}/GetNewerIfExists'
    board = api.get(url.format(board_id, version))
    if board:
        return Board(board, timezone)
    else:
        return None
