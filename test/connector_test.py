# -*- coding: utf-8 -*-

import os
import json
import yaml
import logging
import unittest
import datetime

import leankit


logging.disable(logging.DEBUG)


@unittest.skipUnless(os.path.isfile('credentials.yml'), 'Missing credentials')
class TestAPI(unittest.TestCase):
    def setUp(self):
        with open('credentials.yml') as config:
            credentials = yaml.load(config)
        self.board_id = credentials.pop('board')
        leankit.api.authenticate(**credentials)
        self.board = leankit.api.get('/Boards/{}'.format(self.board_id))
        self.cards = {card['Id']: card for section in ['Lanes', 'Backlog', 'Archive'] for lane in self.board[section] for card in lane['Cards']}
        self.history = {card_id: leankit.api.get('/Card/History/{}/{}'.format(self.board_id, card_id)) for card_id in self.cards}

    def test_authentication(self):
        credentials = leankit.api.session.auth
        leankit.api.session.auth = ('username', 'password')
        with self.assertRaises(ConnectionError) as error:
            leankit.api.get('/Boards')
        self.assertEqual(str(error.exception), 'Server responded with code 401')
        leankit.api.session.auth = credentials

    def test_invalid_url(self):
        self.assertRaises(IOError, leankit.api.get, '/invalid')

    def test_board(self):
        expected = load_file('/Boards/127260303')
        self.assertCountEqual(list(expected.keys()), list(self.board.keys()))

    def test_get_boards(self):
        expected = load_file('/Boards')
        actual = leankit.api.get('/Boards')
        if actual:
            self.assertCountEqual(list(expected[0].keys()), list(actual[0].keys()))

    def test_get_archive(self):
        archive = leankit.api.get('/Board/{}/Archive'.format(self.board_id))
        lanes = [archive[0]['Lane']] + [lane['Lane'] for lane in archive[0]['ChildLanes']]
        cards = [card['Id'] for lane in lanes for card in lane['Cards']]
        duplicates = set(list(self.cards.keys())) - (set(list(self.cards.keys())) - set(cards))
        self.assertEqual(set(), duplicates, "Archive cards downloaded with the rest")

    def test_get_card(self):
        expected = load_file('/Board/127260303/GetCard/127256727')
        for card_id in self.cards:
            actual = leankit.api.get('/Board/{}/GetCard/{}'.format(self.board_id, card_id))
            self.assertCountEqual(list(expected.keys()), list(actual.keys()))

    def test_get_nonexistent_card(self):
        with self.assertRaises(ConnectionError) as error:
            leankit.api.get('/Board/{}/GetCard/123456789'.format(self.board_id))
        self.assertEqual(str(error.exception), 'Error 100: Card not Found.')

    def test_card_last_move(self):
        for card_id, card in self.cards.items():
            try:
                card_last_move = datetime.datetime.strptime(card['LastMove'], '%d/%m/%Y %I:%M:%S %p')
            except ValueError:
                self.fail("Card {} has an invalid LastMove date format: {}".format(card_id, card['LastMove']))
            for event in self.history[card_id]:
                if event['Type'] == 'CardMoveEventDTO':
                    history_last_move = datetime.datetime.strptime(event['DateTime'], '%d/%m/%Y at %I:%M:%S %p')
                    self.assertEqual(history_last_move, card_last_move, "The LastMove for card {} attribute doesn't match the actual last move".format(card_id))
                    break

    def test_card_last_activity(self):
        for card_id, card in self.cards.items():
            try:
                card_last_activity = datetime.datetime.strptime(card['LastActivity'], '%d/%m/%Y %I:%M:%S %p')
            except ValueError:
                self.fail("Card {} has an invalid LastMove date format: {}".format(card_id, card['LastMove']))
            history_last_activity = datetime.datetime.strptime(self.history[card_id][0]['DateTime'], '%d/%m/%Y at %I:%M:%S %p')
            self.assertEqual(history_last_activity, card_last_activity, "The LastActivity attribute for card {} doesn't match the time of the last event".format(card_id))

    def test_card_due_date(self):
        for card_id, card in self.cards.items():
            if card['DueDate']:
                try:
                    datetime.datetime.strptime(card['DueDate'], '%d/%m/%Y')
                except ValueError:
                    self.fail("Card {} has an invalid DueDate date format: {}".format(card_id, card['DueDate']))

    def test_history(self):
        for card_id, history in self.history.items():
            previous_date = datetime.datetime.strptime(history[0]['DateTime'], '%d/%m/%Y at %I:%M:%S %p')
            for event in history[1:]:
                current_date = datetime.datetime.strptime(event['DateTime'], '%d/%m/%Y at %I:%M:%S %p')
                self.assertGreaterEqual(previous_date, current_date, "History events for card {} are not sorted chronologically".format(card_id))


def load_file(url):
    filename = url[1:].replace('/', '-').lower()
    with open('test/responses/{}.json'.format(filename)) as response:
        return json.load(response)



if __name__ == "__main__":
    unittest.main()
