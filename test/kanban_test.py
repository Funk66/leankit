#!/usr/bin/python
# -*- coding: utf-8 -*-

import unittest
import datetime

import leankitmocks as leankit


class TestKanban(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.board = leankit.Board(100000000, timezone='Europe/Berlin')
        cls.board.get_archive()

    def test_get_boards(self):
        boards = leankit.get_boards()
        self.assertEqual(list, type(boards))

    def test_board_str(self):
        self.assertEqual('Board 100000000', str(self.board))

    def test_board_tags(self):
        self.assertEqual(['Tag1', 'Tag2'], self.board.available_tags)

    def test_board_archive_top_level_lane(self):
        self.assertEqual(self.board.lanes[100001008],
                         self.board.archive_top_level_lane)

    def test_board_backlog_top_level_lane(self):
        self.assertEqual(self.board.lanes[100001001],
                         self.board.backlog_top_level_lane)

    def test_board_archive_lanes(self):
        self.assertEqual(3, len(self.board.archive_lanes))

    def test_board_get_card(self):
        self.assertEqual(self.board.cards[100010001]['Id'],
                         self.board.get_card(100010001)['Id'])

    def test_lane_str(self):
        lane = self.board.lanes[100001006]
        self.assertEqual(lane.path, str(lane))

    def test_lane_path(self):
        self.assertEqual('Lane 2', self.board.lanes[100001003].path)
        self.assertEqual('Lane 2::Sublane 2.2::Sublane 2.2.1',
                         self.board.lanes[100001006].path)

    def test_lane_top_lane(self):
        self.assertEqual(self.board.lanes[100001003],
                         self.board.lanes[100001006].top_lane)
        self.assertEqual(self.board.lanes[100001003],
                         self.board.lanes[100001003].top_lane)

    def test_lane_parent_lane(self):
        self.assertEqual(None, self.board.lanes[100001003].parent_lane)
        self.assertEqual(self.board.lanes[100001003],
                         self.board.lanes[100001005].parent_lane)

    def test_lane_children(self):
        self.assertEqual(2, len(self.board.lanes[100001003].children))
        self.assertEqual([], self.board.lanes[100001006].children)

    def test_lane_ascendants(self):
        self.assertEqual([], (self.board.lanes[100001003].ascendants))
        self.assertEqual(2, len(self.board.lanes[100001006].ascendants))

    def test_lane_descendants(self):
        self.assertEqual(4, len(self.board.lanes[100001003].descendants))
        self.assertEqual([], self.board.lanes[100001006].descendants)

    def test_card_str(self):
        self.assertEqual('100010001', str(self.board.cards[100010001]))

    def test_card_history(self):
        self.assertEqual(7, len(self.board.cards[100010001].history))

    def test_card_last_move(self):
        expected = "2017-02-27 13:58:08+01:00"
        actual = str(self.board.cards[100010001].last_move)
        self.assertEqual(expected, actual)

    def test_card_last_activity(self):
        expected = "2017-03-30 11:21:01+02:00"
        actual = str(self.board.cards[100010001].last_activity)
        self.assertEqual(expected, actual)

    def test_card_due_date(self):
        self.assertEqual(None, self.board.cards[100010001].due_date)

    def test_card_date_archived(self):
        date_archived = datetime.date(2017, 2, 27)
        self.assertEqual(date_archived, self.board.cards[100010003].date_archived)
        self.assertEqual(None, self.board.cards[100010001].date_archived)

    def test_card_tags(self):
        self.assertEqual(['Tag1', 'Tag2'], self.board.cards[100010001].tags)
        self.assertEqual([], self.board.cards[100010002].tags)

    def test_event_date_time(self):
        expected = "2017-03-30 11:21:01+02:00"
        actual = str(self.board.cards[100010001].history[-1].date_time)
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
