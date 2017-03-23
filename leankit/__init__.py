# -*- coding: utf-8 -*-

import re
import pytz
import logging
import operator
from datetime import datetime
from cached_property import cached_property

from .connector import api


log = logging.getLogger(__name__)


class KanbanError(Exception):
    """ Error thrown when performing a non-valid operation """


class Converter(object):
    """ Convert JSON returned by Leankit to Python classes.

    JSON returned by Leankit is in the form of a dict with CamelCase
    named values which are converted to lowercase underscore-separated
    class attributes.
    """
    attributes = []

    def __init__(self, raw_data, board):
        self.board = board
        self.raw_data = raw_data
        for attr in self.attributes:
            setattr(self, self.prettify_name(attr), raw_data.get(attr, ''))

    @staticmethod
    def prettify_name(camelcase):
        camelcase = camelcase.replace('ID', '_id')
        if len(camelcase) > 1:
            return re.sub('([A-Z])', lambda match: '_' + match.group(1).lower(),
                          camelcase[0].lower() + camelcase[1:])
        else:
            return camelcase.lower()

    @staticmethod
    def to_camel_case(name):
        if len(name) > 1:
            return re.sub('(_[a-z])', lambda match: match.group(1)[1:].upper(),
                          name[0].upper() + name[1:])
        else:
            return name.upper()

    def jsonify(self):
        data = {'LastUpdate': datetime.today()}
        for attr in self.attributes:
            data[attr] = self.raw_data[attr]
        if self.board:
            data['BoardId'] = self.board.id
        return data


class User(Converter):
    attributes = ['Id', 'UserName', 'FullName', 'EmailAddress',
                  'Enabled', 'IsDeleted', 'RoleName', 'GravatarLink']

    def __repr__(self):
        return self.user_name


class CardType(Converter):
    attributes = ['Id', 'Name', 'ColorHex']

    def __repr__(self):
        return self.name


class ClassOfService(Converter):
    attributes = ['Id', 'Title', 'ColorHex']

    def __repr__(self):
        return self.title


class OrganizationActivity(Converter):
    attributes = ['Id', 'Name']

    def __repr__(self):
        return self.name


class Card(Converter):
    attributes = ['Id', 'Title', 'Description', 'PriorityText',
                  'ClassOfServiceId', 'Tags', 'Color', 'Size',
                  'ExternalCardID', 'AssignedUserId', 'IsBlocked',
                  'BlockReason', 'Priority', 'TypeName', 'TypeId',
                  'ClassOfServiceTitle', 'AssignedUserName']

    def __init__(self, card_dict, lane, board):
        super().__init__(card_dict, board)
        self.lane = lane
        self.date_archived_str = card_dict['DateArchived']
        self.last_move_str = card_dict['LastMove']
        self.last_activity_str = card_dict['LastActivity']
        self.due_date_str = card_dict['DueDate']
        self.actual_start_date_str = card_dict['ActualStartDate']
        self.actual_finish_date_str = card_dict['ActualFinishDate']
        self.archived = card_dict.get('Archived', False)
        self.board.cards[self.id] = self

    def __repr__(self):
        return str(self.external_card_id or self.id)

    def jsonify(self):
        data = super().jsonify()
        dates = ['LastActivity', 'LastMove', 'DateArchived', 'DueDate']
        for date in dates:
            data[date] = getattr(self, self.prettify_name(date))
        return data

    @cached_property
    def history(self):
        history = api.get("/Card/History/{0.board.id}/{0.id}".format(self))
        for event in history:
            date = datetime.strptime(event['DateTime'], '%d/%m/%Y at %I:%M:%S %p')
            event['DateTime'] = self.board.timezone.localize(date)
            event['Position'] = len(history) - history.index(event)
            event['BoardId'] = self.board.id
        return list(reversed(history))

    @cached_property
    def comments(self):
        return api.get("/Card/GetComments/{0.board.id}/{0.id}".format(self))

    @property
    def due_date(self):
        if self.due_date_str:
            date = datetime.strptime(self.due_date_str, '%d/%m/%Y %I:%M:%S %p')
            return self.board.timezone.localize(date)
        else:
            return ''

    @property
    def last_move(self):
        if self.last_move_str:
            date = datetime.strptime(self.last_move_str, '%d/%m/%Y %I:%M:%S %p')
            return self.board.timezone.localize(date)
        else:
            return ''

    @property
    def last_activity(self):
        if self.last_activity_str:
            date = datetime.strptime(self.last_activity_str,
                                     '%d/%m/%Y %I:%M:%S %p')
            return self.board.timezone.localize(date)
        else:
            return ''

    @property
    def date_archived(self):
        if self.date_archived_str:
            return datetime.strptime(self.date_archived_str, '%d/%m/%Y')
        else:
            return ''

    @property
    def actual_start_date(self):
        if self.actual_start_date_str:
            date = datetime.strptime(self.actual_start_date_str,
                                     '%d/%m/%Y %I:%M:%S %p')
            return self.board.timezone.localize(date)
        else:
            return ''

    @property
    def actual_finish_date(self):
        if self.actual_finish_date_str:
            date = datetime.strptime(self.actual_finish_date_str,
                                     '%d/%m/%Y %I:%M:%S %p')
            return self.board.timezone.localize(date)
        else:
            return ''


class Lane(Converter):
    attributes = ['Id', 'Title', 'Index', 'Orientation', 'ParentLaneId',
                  'ChildLaneIds', 'SiblingLaneIds', 'ActivityId',
                  'ActivityName', 'LaneState', 'Width']

    def __init__(self, lane_dict, board):
        super().__init__(lane_dict, board)
        self.cards = [Card(card_dict, self, board) for card_dict
                      in lane_dict['Cards'] if card_dict['TypeId']]
        self.area = lane_dict.get('Area', 'wip')

    def __repr__(self):
        return self.path

    @property
    def path(self):
        titles = [self.title] + [lane.title for lane in self.ascendants]
        return '::'.join(reversed(titles))

    @property
    def main_lane(self):
        return ([self] + self.ascendants)[-1]

    @property
    def parent(self):
        return self.board.lanes.get(self.parent_lane_id)

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
    def children(self):
        return [self.board.lanes[lane_id] for lane_id in self.child_lane_ids]

    @property
    def role(self):
        return 'parent' if self.children else 'child'

    @property
    def descendants(self):
        """ Returns a list of all child lanes sorted in descending order """
        def sublanes(lane, array):
            for child in lane.children:
                array.append(child)
                sublanes(child, array)
            return array

        return sublanes(self, [])

    @property
    def parent_lane_ids(self):
        id_list = []
        lane = self.parent
        while lane:
            id_list.append(lane.id)
            lane = lane.parent
        return id_list

    def jsonify(self):
        data = super().jsonify()
        data['Area'] = self.area
        return data

    def propagate(self, key, value):
        setattr(self, key, value)
        for lane in self.descendants:
            setattr(lane, key, value)


class Board(Converter):
    attributes = ['Id', 'Title', 'AvailableTags', 'BacklogTopLevelLaneId',
                  'ArchiveTopLevelLaneId', 'TopLevelLaneIds', 'Version']

    def __init__(self, board, archive=False, timezone='UTC'):
        if isinstance(board, int):
            board = api.get('/Boards/{}'.format(board))
        super().__init__(board, None)
        self.cards = {}
        self.lanes = self.populate('Lanes', Lane)
        self.lanes.update(self.populate('Backlog', Lane))
        self.lanes.update(self.populate('Archive', Lane))
        self.users = self.populate('BoardUsers', User)
        self.card_types = self.populate('CardTypes', CardType)
        self.classes_of_service = self.populate('ClassesOfService', ClassOfService)
        self.organization_activities = self.populate('OrganizationActivities', OrganizationActivity)
        self.timezone = pytz.timezone(timezone)
        if archive:
            self.get_archive()

    def __repr__(self):
        return self.title

    @property
    def deck(self):
        return list(self.cards.values())

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
        archive['Lane']['Area'] = 'archive'
        main_archive_lane = Lane(archive['Lane'], self)
        self.lanes[main_archive_lane.id] = main_archive_lane
        self.raw_data['Lanes'].append(archive['Lane'])
        for lane_dict in archive['ChildLanes']:
            lane_dict['Lane']['Area'] = 'archive'
            lane = Lane(lane_dict['Lane'], self)
            self.lanes[lane.id] = lane
            self.raw_data['Lanes'].append(lane_dict['Lane'])

    def get_card(self, card_id):
        url = '/Board/{}/GetCard/{}'
        card_dict = api.get(url.format(str(self.id), card_id))
        assert self.lanes.get(card_dict['LaneId']), \
            "Lane {} does not exist".format(card_dict['LaneId'])
        lane = self.lanes[card_dict['LaneId']]  # TODO: replace card in lane
        card = Card(card_dict, lane, self)
        return card

    def find(self, array, attribute, value, mode='eq', case=True):
        matches = []
        for item in getattr(self, array).values():
            actual_value = getattr(item, attribute)
            if case and isinstance(attribute, str) \
                    and isinstance(actual_value, str):
                actual_value = actual_value.lower()
                value = value.lower()
            if getattr(operator, mode)(actual_value, value):
                matches.append(item)
        return matches[0] if len(matches) == 1 else matches

    def strptime(self, date_str, time=True):
        if time:
            date = datetime.strptime(date_str, '%d/%m/%Y at %I:%M:%S %p')
            return self.timezone.localize(date)
        else:
            return datetime.strptime(date_str, '%d/%m/%Y')


def get_boards():
    return api.get('/Boards')


def get_newer_if_exists(board_id, version):
    """ Downloads a board if a newer version number exists """
    url = '/Board/{}/BoardVersion/{}/GetNewerIfExists'
    board = api.get(url.format(board_id, version))
    if board:
        return Board(board)
    else:
        return None
