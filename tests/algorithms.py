#!/usr/bin/env python

import unittest
import symath

class TestAlgorithms(unittest.TestCase):

  def setUp(self):
    pass

  def test_edit_distance(self):
    from symath.algorithms.editdistance import edit_distance,edit_substitutions
    x,y,z = symath.symbols('x y z')
    a,b,c = symath.wilds('a b c')
    self.assertEqual(edit_distance(x(x, y, x), y(x, x, x)), 2)
    self.assertEqual(edit_distance(x(y, x), x(y, y, x)), 1)
    self.assertEqual(edit_distance(x(y, x), x(x)), 1)
    self.assertEqual(edit_distance(x(y, y, x), x(x)), 2)
    self.assertEqual(edit_distance(a, x(y, y)), 0)
    self.assertEqual(edit_distance(a(x, x), x(y, x)), 1)

    self.assertNotEqual(edit_distance(y(x(a, b), x(b, a)), y(x(a, b), x(a, b))), 0)
    self.assertEqual(edit_distance(y(x(a, b), x(b, a)), y(x(a, b), x(a, b))), 2)
    self.assertEqual(edit_distance(y(x(a, b), x(b, a)), x(x(a, b), x(a, b))), 3)

if __name__ == '__main__':
  unittest.main()
