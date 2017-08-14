# -*- coding: utf-8 -*-

import json
import unittest
from unittest.mock import patch, Mock

import leankit


class TestKanban(unittest.TestCase):
    def setUp(self):
        patcher = patch('leankit.api.get', Mock(side_effect=get_file))
        self.api = patcher.start()
        self.addCleanup(patcher.stop)
        self.board = leankit.Board(127260303, timezone='Europe/Berlin')
        self.toplane = self.board.lanes[127250640]
        self.midlane = self.board.lanes[127250757]
        self.sublane = self.board.lanes[127250758]

    def test_get_boards(self):
        leankit.get_boards()
        self.api.assert_called_with('/Boards')

    def test_get_newer_if_exists(self):
        self.assertEqual(None, leankit.get_newer_if_exists(127260303, 14))
        self.api.assert_called_with('/Board/127260303/BoardVersion/14/GetNewerIfExists')

    def test_board(self):
        self.api.assert_called_with('/Boards/127260303')

    def test_board_title(self):
        self.assertEqual('API test', str(self.board))

    def test_board_tags(self):
        self.assertEqual(['Tag1'], self.board.available_tags)

    def test_board_archive_lanes(self):
        archive_lanes = [self.board.lanes[lane_id] for lane_id in [127250638, 127250762, 127250761]]
        self.assertEqual(archive_lanes, self.board.archive_lanes)

    def test_board_get_archive(self):
        self.assertEqual(2, len(self.board.cards))
        self.board.get_archive()
        self.api.assert_called_with('/Board/127260303/Archive')
        self.assertEqual(3, len(self.board.cards))

    def test_board_get_recent_archive(self):
        cards = self.board.get_recent_archive()
        self.assertEqual(1, len(cards))
        self.assertIsInstance(cards[0], leankit.kanban.Card)
        self.api.assert_called_with('/Board/127260303/ArchiveCards')

    def test_board_get_card(self):
        self.board.get_card(127256727)
        self.api.assert_called_with('/Board/127260303/GetCard/127256727')
        self.assertIsNone(self.board.cards[127256727].class_of_service_id)

    def test_lane_path(self):
        self.assertEqual('Lane 2', self.toplane.path)
        self.assertEqual('Lane 2::Sublane 2.2::Sublane 2.2.2', self.sublane.path)

    def test_lane_top_lane(self):
        self.assertEqual(self.toplane, self.sublane.top_lane)
        self.assertEqual(self.toplane, self.toplane.top_lane)

    def test_lane_parent(self):
        self.assertEqual(self.midlane, self.sublane.parent_lane)
        self.assertEqual(None, self.toplane.parent_lane)

    def test_lane_children(self):
        children = [self.board.lanes[lane_id] for lane_id in [127250760, 127250757]]
        self.assertEqual(children, self.toplane.children)
        self.assertEqual([], self.sublane.children)

    def test_lane_ascendants(self):
        self.assertEqual([], self.toplane.ascendants)
        self.assertEqual([self.midlane, self.toplane], self.sublane.ascendants)

    def test_lane_descendants(self):
        descendants = [self.board.lanes[lane_id] for lane_id in [127250760, 127250757, 127250759, 127250758]]
        self.assertEqual(descendants, self.toplane.descendants)
        self.assertEqual([], self.sublane.descendants)

    def test_card_history(self):
        self.board.cards[127256728].history
        self.api.assert_called_with('/Card/History/127260303/127256728')

    def test_card_comment(self):
        self.board.cards[127256728].comments
        self.api.assert_called_with('/Card/GetComments/127260303/127256728')

    def test_card_last_move(self):
        expected = "2017-02-27 13:58:08+01:00"
        actual = str(self.board.cards[127256728].last_move)
        self.assertEqual(expected, actual)

    def test_card_tags(self):
        self.assertEqual(['Tag1'], self.board.cards[127256728].tags)
        self.assertEqual([], self.board.cards[127256333].tags)


def get_file(url):
    filename = url[1:].replace('/', '-').lower()
    with open('test/responses/{}.json'.format(filename)) as response:
        return json.load(response)


if __name__ == "__main__":
    unittest.main()
