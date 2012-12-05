#!/usr/bin/env python

import unittest
import symath

class TestAlgorithms(unittest.TestCase):

  def setUp(self):
    pass

  def test_edit_distance(self):
    from symath.algorithms.editdistance import edit_distance
    x,y = symath.symbols('x y')
    self.assertEqual(edit_distance(x(x, y, x), y(x, x, x)), 2)
    self.assertEqual(edit_distance(x(y, x), x(y, y, x)), 1)
    self.assertEqual(edit_distance(x(y, x), x(x)), 1)
    self.assertEqual(edit_distance(x(y, y, x), x(x)), 2)

if __name__ == '__main__':
  unittest.main()
