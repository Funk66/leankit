#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import pytz
import logging
from dateutil.parser import parse
from datetime import time
from cached_property import cached_property

from .connector import api


log = logging.getLogger(__name__)


class KanbanError(Exception):
    """ Error thrown when performing a non-valid operation """


class Converter(object):
    def __init__(self, raw_data, board):
        self.board = board
        self.raw_data = raw_data
        for attr in raw_data:
            setattr(self, self.prettify_name(attr), raw_data.get(attr, ''))

    def __repr__(self):
        return str(self.id)

    @staticmethod
    def prettify_name(camelcase):
        camelcase = camelcase.replace('ID', '_id')
        if len(camelcase) > 1:
            return re.sub('([A-Z])', lambda match: '_' + match.group(1).lower(),
                          camelcase[0].lower() + camelcase[1:])
        else:
            return camelcase.lower()


class User(Converter):
    def __str__(self):
        return self.user_name


class CardType(Converter):
    def __str__(self):
        return self.name


class ClassOfService(Converter):
    def __str__(self):
        return self.title


class Card(Converter):
    date_fields = ['last_move', 'last_activity', 'create_date', 'date_archived',
                   'due_date', 'last_comment', 'start_date',
                   'actual_start_date', 'actual_finish_date']

    def __init__(self, data, lane, board):
        super().__init__(data, board)
        self.lane = lane
        self.board = board
        self.type = board.card_types[data['TypeId']]
        self.assigned_user = board.users.get(data['AssignedUserId'])
        self.assigned_users = [board.users[u] for u in data['AssignedUserIds']]
        self.class_of_service = board.classes_of_service.get(data['ClassOfServiceId'])
        for date in self.date_fields:
            if hasattr(self, date):
                if getattr(self, date):
                    dt = parse(getattr(self, date), dayfirst=True)
                    if dt.time() == time(0):
                        self.__dict__[date] = dt.date()
                    elif board.timezone:
                        self.__dict__[date] = board.timezone.localize(dt)
                    else:
                        self.__dict__[date] = dt

        tag_str = self.raw_data['Tags']
        self.tags = tag_str.strip(',').split(',') if tag_str else []
        self.board.cards[self.id] = self

    def __str__(self):
        return str(self.external_card_id or self.id)

    @cached_property
    def history(self):
        history = api.get("/Card/History/{0.board.id}/{0.id}".format(self))
        for event in history:
            date = parse(event['DateTime'], dayfirst=True)
            if self.board.timezone:
                date = self.board.timezone.localize(date)
            event['DateTime'] = date
            event['Position'] = len(history) - history.index(event)
            event['BoardId'] = self.board.id
        return list(reversed(history))

    @cached_property
    def comments(self):
        return api.get("/Card/GetComments/{0.board.id}/{0.id}".format(self))


class Lane(Converter):
    def __init__(self, data, board):
        super().__init__(data, board)
        self.cards = [Card(card_dict, self, board) for card_dict
                      in data['Cards'] if card_dict['TypeId']]

    def __str__(self):
        return self.path

    @property
    def path(self):
        titles = [self.title] + [lane.title for lane in self.ascendants]
        return '::'.join(reversed(titles))

    @property
    def top_lane(self):
        return ([self] + self.ascendants)[-1]

    @property
    def parent(self):
        return self.board.lanes.get(self.parent_lane_id)

    @property
    def children(self):
        return [self.board.lanes[lane_id] for lane_id in self.child_lane_ids]

    @property
    def ascendants(self):
        """ Returns a list of all parent lanes sorted in ascending order """
        lanes = []
        lane = self.parent
        while lane:
            lanes.append(lane)
            lane = lane.parent
        return lanes

    @property
    def descendants(self):
        """ Returns a list of all child lanes sorted in descending order """
        def sublanes(lane, array):
            for child in lane.children:
                array.append(child)
                sublanes(child, array)
            return array

        return sublanes(self, [])


class Board(Converter):
    def __init__(self, board, timezone=None):
        if isinstance(board, int):
            board = api.get('/Boards/{}'.format(board))
        super().__init__(board, None)
        self.cards = {}
        tag_str = self.raw_data['AvailableTags']
        self.tags = tag_str.strip(',').split(',') if tag_str else []
        self.timezone = pytz.timezone(timezone) if timezone else None
        self.users = self.populate('BoardUsers', User)
        self.card_types = self.populate('CardTypes', CardType)
        self.classes_of_service = self.populate('ClassesOfService', ClassOfService)
        self.lanes = self.populate('Lanes', Lane)
        self.lanes.update(self.populate('Backlog', Lane))
        self.lanes.update(self.populate('Archive', Lane))

    def __str__(self):
        return self.title

    @property
    def top_level_lanes(self):
        return [self.lanes[lane_id] for lane_id in self.top_level_lane_ids]

    @cached_property
    def archive_lanes(self):
        if self.archive_top_level_lane_id not in self.lanes:
            raise KanbanError("Archive lanes not available")
        archive_lane = self.lanes[self.archive_top_level_lane_id]
        return [archive_lane] + archive_lane.descendants

    @cached_property
    def backlog_lanes(self):
        if self.backlog_top_level_lane_id not in self.lanes:
            raise KanbanError("Backlog lanes not available")
        backlog_lane = self.lanes[self.backlog_top_level_lane_id]
        return [backlog_lane] + backlog_lane.descendants

    @property
    def sorted_lanes(self):
        lanes = []
        lanes += self.backlog_lanes
        for lane in self.top_level_lanes:
            lanes += [lane] + lane.descendants
        lanes += self.archive_lanes
        return lanes

    def populate(self, key, element):
        items = {}
        for item in self.raw_data[key]:
            instance = element(item, self)
            items[instance.id] = instance
        return items

    def get_archive(self):
        archive = api.get('/Board/{0.id}/Archive'.format(self))[0]
        main_archive_lane = Lane(archive['Lane'], self)
        self.lanes[main_archive_lane.id] = main_archive_lane
        self.raw_data['Lanes'].append(archive['Lane'])
        for lane_dict in archive['ChildLanes']:
            lane = Lane(lane_dict['Lane'], self)
            self.lanes[lane.id] = lane
            self.raw_data['Lanes'].append(lane_dict['Lane'])

    def get_recent_archive(self):
        archive = api.get('/Board/{0.id}/ArchiveCards'.format(self))
        return [Card(card, self.lanes.get(card['LaneId']), self)
                for card in archive if card['TypeId']]

    def get_card(self, card_id):
        url = '/Board/{}/GetCard/{}'
        card_dict = api.get(url.format(str(self.id), card_id))
        assert self.lanes.get(card_dict['LaneId']), \
            "Lane {} does not exist".format(card_dict['LaneId'])
        lane = self.lanes[card_dict['LaneId']]  # TODO: replace card in lane
        card = Card(card_dict, lane, self)
        return card


def get_boards():
    return api.get('/Boards')


def get_newer_if_exists(board_id, version, timezone='UTC'):
    """ Downloads a board if a newer version number exists """
    url = '/Board/{}/BoardVersion/{}/GetNewerIfExists'
    board = api.get(url.format(board_id, version))
    if board:
        return Board(board, timezone=timezone)
    else:
        return None
