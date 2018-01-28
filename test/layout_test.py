import unittest

import leankitmocks as leankit
from leankit.kanban import Lane


class TestKanban(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.board = leankit.Board(300000000)
        cls.lanes = {lane["Title"]: lane for lane in cls.board.lanes.values()}

    def test_lane_width(self):
        width = Lane.WIDTH * 4 + Lane.BORDER
        self.assertEqual(width, self.lanes["Backlog"].width)
        width = Lane.WIDTH * 3 + Lane.BORDER * 2
        self.assertEqual(width, self.lanes["Lane 3"].width)

    def test_lane_height(self):
        height = Lane.HEADER * 7 + Lane.BORDER * 9 + Lane.BOX * 3
        self.assertEqual(height, self.lanes["Backlog"].height)
        self.assertEqual(height, self.lanes["Lane 1"].height)
        height = Lane.HEADER * 6 + Lane.BORDER * 8 + Lane.BOX * 3
        self.assertEqual(height, self.lanes["Lane 2.1"].height)
        height = Lane.HEADER * 4 + Lane.BORDER * 5 + Lane.BOX * 2
        self.assertEqual(height, self.lanes["Lane 3.1.1"].height)
        height = Lane.HEADER + Lane.BORDER + Lane.BOX
        self.assertEqual(height, self.lanes["Lane 3.1.2.2.2"].height)

    def test_lane_left(self):
        self.assertEqual(0, self.lanes["Backlog"].left)
        left = Lane.WIDTH * 4 + Lane.BORDER * 2
        self.assertEqual(left, self.lanes["Lane 1"].left)
        left = Lane.WIDTH * 10 + Lane.BORDER * 7
        self.assertEqual(left, self.lanes["Lane 3.1.2.2.2"].left)

    def test_lane_right(self):
        right = Lane.WIDTH * 4 + Lane.BORDER
        self.assertEqual(right, self.lanes["Backlog"].right)
        right = Lane.WIDTH * 5 + Lane.BORDER * 2
        self.assertEqual(right, self.lanes["Lane 1"].right)
        right = Lane.WIDTH * 11 + Lane.BORDER * 7
        self.assertEqual(right, self.lanes["Lane 3.1.2.2.2"].right)

    def test_lane_top(self):
        self.assertEqual(0, self.lanes["Backlog"].top)
        top = Lane.HEADER + Lane.BORDER
        self.assertEqual(top, self.lanes["Lane 2.1"].top)
        top = Lane.HEADER * 5 + Lane.BORDER * 6 + Lane.BOX
        self.assertEqual(top, self.lanes["Lane 3.1.2.2.2"].top)

    def test_lane_bottom(self):
        bottom = Lane.HEADER * 2 + Lane.BORDER * 2 + Lane.BOX
        self.assertEqual(bottom, self.lanes["Backlog"].bottom)
        bottom = Lane.HEADER + Lane.BORDER + Lane.BOX
        self.assertEqual(bottom, self.lanes["Lane 1"].bottom)
        bottom = Lane.HEADER * 7 + Lane.BORDER * 9 + Lane.BOX * 3
        self.assertEqual(bottom, self.lanes["Lane 3"].bottom)
        self.assertEqual(bottom, self.lanes["Lane 3.2"].bottom)
        bottom = Lane.HEADER * 6 + Lane.BORDER * 7 + Lane.BOX * 2
        self.assertEqual(bottom, self.lanes["Lane 3.1"].bottom)
        self.assertEqual(bottom, self.lanes["Lane 3.1.2"].bottom)
        self.assertEqual(bottom, self.lanes["Lane 3.1.2.2.1"].bottom)
