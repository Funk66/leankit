#!/usr/bin/python
# -*- coding: utf-8 -*-

from pytz import timezone as tz
from dateutil.parser import parse
from datetime import time
from cached_property import cached_property

from . import log
from . import api


class KanbanError(Exception):
    """ Error thrown when performing a non-valid operation """


class Converter(dict):
    def __init__(self, data, board):
        super().__init__(**data)
        self.board = board

    def __repr__(self):
        return '<{0.__class__.__name__} {0.id}>'.format(self)

    def __hash__(self):
        return hash(repr(self))

    def __getattr__(self, name):
        try:
            value = self[self._capitalize_(name)]
            return None if name.endswith('_id') and value is 0 else value
        except KeyError as error:
            raise AttributeError(error)

    def __setattr__(self, name, value):
        self[self._capitalize_(name)] = value

    @staticmethod
    def _capitalize_(snake_case):
        return snake_case.title().replace('_', '')


class User(Converter):
    def __str__(self):
        return self.user_name


class CardType(Converter):
    def __str__(self):
        return self.name


class ClassOfService(Converter):
    def __str__(self):
        return self.title


class Event(Converter):
    def __init__(self, data, board):
        super().__init__(data, board)
        self.date_time = parse(self.date_time, dayfirst=True)
        if self.board.timezone:
            self.date_time = self.board.timezone.localize(self.date_time)

    def __repr__(self):
        return '<{0.__class__.__name__} {0.card.id}-{0.position}>'.format(self)

    @property
    def card(self):
        return self.board.cards[self.card_id]

    @property
    def to_lane(self):
        return self.board.lanes.get(self.to_lane_id)

    @property
    def from_lane(self):
        return self.board.lanes.get(self.from_lane_id)

    @property
    def user(self):
        return self.board.users.get(self.user_id)

    @property
    def position(self):
        return self.card.history.index(self)


class Card(Converter):
    _date_fields_ = ['LastMove', 'LastActivity', 'CreateDate', 'DateArchived',
                     'DueDate', 'LastComment', 'StartDate', 'ActualStartDate',
                     'ActualFinishDate']

    def __init__(self, data, lane, board):
        super().__init__(data, board)
        self.lane = lane
        self.tags = self.tags.strip(',').split(',') if self.tags else []
        self.board.cards[self.id] = self
        for date in self._date_fields_:
            if date in self:
                if self[date]:
                    dt = parse(self[date], dayfirst=True)
                    if dt.time() == time(0):
                        self[date] = dt.date()
                    elif board.timezone:
                        self[date] = board.timezone.localize(dt)
                    else:
                        self[date] = dt
                else:
                    self[date] = None

    def __str__(self):
        return str(self.get('ExternalCardID', self.id))

    @cached_property
    def history(self):
        history = api.get("/Card/History/{0.board.id}/{0.id}".format(self))
        return list(reversed([Event(event, self.board) for event in history]))

    @cached_property
    def comments(self):
        return api.get("/Card/GetComments/{0.board.id}/{0.id}".format(self))

    @property
    def type(self):
        return self.board.card_types[self.type_id]

    @property
    def class_of_service(self):
        return self.board.classes_of_service.get(self.class_of_service_id)

    @property
    def assigned_user(self):
        return self.board.users.get(self.assigned_user_id)


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
    def parent_lane(self):
        return self.board.lanes.get(self.parent_lane_id)

    @property
    def children(self):
        return [self.board.lanes[lane_id] for lane_id in self.child_lane_ids]

    @property
    def ascendants(self):
        """ Returns a list of all parent lanes sorted in ascending order """
        lanes = []
        lane = self.parent_lane
        while lane:
            lanes.append(lane)
            lane = lane.parent_lane
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
            log.debug('Downloading board {}'.format(board))
            board = api.get('/Boards/{}'.format(board))
        super().__init__(board, self)
        self.cards = {}
        self.timezone = tz(timezone) if timezone else None
        self.users = self._populate_('BoardUsers', User)
        self._populate_('CardTypes', CardType)
        self._populate_('ClassesOfService', ClassOfService)
        self._populate_('Lanes', Lane)
        self.lanes.update(self._populate_('Backlog', Lane))
        self.lanes.update(self._populate_('Archive', Lane))
        tags = self.available_tags
        self.available_tags = tags.strip(',').split(',') if tags else []

    def __str__(self):
        return self.title

    def _populate_(self, key, element):
        items = {}
        for item in self[key]:
            instance = element(item, self)
            items[instance.id] = instance
        self[key] = items
        return items

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

    def get_archive(self):
        archive = api.get('/Board/{0.id}/Archive'.format(self))[0]
        main_archive_lane = Lane(archive['Lane'], self)
        self.lanes[main_archive_lane.id] = main_archive_lane
        for lane_dict in archive['ChildLanes']:
            lane = Lane(lane_dict['Lane'], self)
            self.lanes[lane.id] = lane

    def get_recent_archive(self):
        archive = api.get('/Board/{0.id}/ArchiveCards'.format(self))
        return [Card(card, self.lanes.get(card['LaneId']), self)
                for card in archive if card['TypeId']]

    def get_card(self, card_id):
        url = '/Board/{}/GetCard/{}'
        card_dict = api.get(url.format(str(self.id), card_id))
        lane = self.lanes.get(card_dict['LaneId'])  # TODO: replace card in lane
        card = Card(card_dict, lane, self)
        return card
