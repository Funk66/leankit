from logging import getLogger
from datetime import datetime
from pytz import timezone as tz
from cached_property import cached_property

from . import api


class KanbanError(Exception):
    """ Error thrown when performing a non-valid operation """


class Converter(dict):
    _attrs_, _items_ = {}, {}

    def __init__(self, data, board):
        super().__init__(**data)
        self.board = board

    def __repr__(self):
        return '<{0.__class__.__name__} {0.id}>'.format(self)

    def __hash__(self):
        return hash(repr(self))

    def __getitem__(self, key):
        if key in self._attrs_:
            value = super().__getitem__(key)
            return getattr(self, '_' + self._attrs_[key] + '_')(value)
        elif key in self._items_:
            return self.board[self._items_[key]].get(int(self[key + 'Id']))
        else:
            return super().__getitem__(key)

    def __getattr__(self, name):
        key = name.title().replace('_', '')
        try:
            return self[key]
        except KeyError:
            raise AttributeError(name)

    @staticmethod
    def _list_(value):
        return [val for val in value.strip(',').split(',') if val]

    @staticmethod
    def _date_(value):
        return datetime.strptime(value, '%d/%m/%Y').date() if value else None

    def _datetime_(self, value):
        if value:
            time = datetime.strptime(value, '%d/%m/%Y %I:%M:%S %p')
            if self.board.timezone:
                return self.board.timezone.localize(time)
            return time
        return None

    @property
    def raw_data(self):
        return {key: self[key] for key in self.keys()}


class User(Converter):
    def __str__(self):
        return self.user_name


class CardType(Converter):
    def __str__(self):
        return self['Name']


class ClassOfService(Converter):
    def __str__(self):
        return self['Title']


class Event(Converter):
    _attrs_ = {'DateTime': 'datetime'}
    _items_ = {'User': 'Users', 'ToLane': 'Lanes', 'FromLane': 'Lanes'}

    def __repr__(self):
        return '<{0.__class__.__name__}>'.format(self)

    def _datetime_(self, value):
        time = datetime.strptime(value, '%d/%m/%Y at %I:%M:%S %p')
        if self.board.timezone:
            return self.board.timezone.localize(time)
        return time


class Card(Converter):
    _attrs_ = {'LastMove': 'datetime', 'LastActivity': 'datetime',
               'CreateDate': 'date', 'DateArchived': 'date', 'DueDate': 'date',
               'LastComment': 'date', 'StartDate': 'date', 'Tags': 'list',
               'ActualStartDate': 'datetime', 'ActualFinishDate': 'datetime'}
    _items_ = {'Type': 'CardTypes', 'AssignedUser': 'Users',
               'ClassOfService': 'ClassesOfService'}

    def __init__(self, data, lane, board):
        super().__init__(data, board)
        self.lane = lane
        self.board.cards[self.id] = self

    def __str__(self):
        return str(self.get('ExternalCardID', self.id) or self.id)

    @cached_property
    def history(self):
        events = api.get("/Card/History/{0.board.id}/{0.id}".format(self))
        return [Event(event, self.board) for event in reversed(events)]

    @cached_property
    def comments(self):
        return api.get("/Card/GetComments/{0.board.id}/{0.id}".format(self))


class Lane(Converter):
    _items_ = {'ParentLane': 'Lanes'}

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
    _attrs_ = {'AvailableTags': 'list'}
    _items_ = {'BacklogTopLevelLane': 'Lanes', 'ArchiveTopLevelLane': 'Lanes'}

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

    def __str__(self):
        return self['Title']

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

    @property
    def archive_lanes(self):
        if self.archive_top_level_lane_id not in self.lanes:
            raise KanbanError("Archive lanes not available")
        archive_lane = self.archive_top_level_lane
        return [archive_lane] + archive_lane.descendants

    @property
    def backlog_lanes(self):
        if self.backlog_top_level_lane_id not in self.lanes:
            raise KanbanError("Backlog lanes not available")
        backlog_lane = self.backlog_top_level_lane
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


log = getLogger(__name__)
