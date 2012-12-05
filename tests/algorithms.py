#!/usr/bin/env python

import unittest
import symath
import symath.util as util

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

  def test_print_edit_distance_metric(self):
    import symath.algorithms.editdistance as ed
    from numpy import *
    ed._tuple_edit_distance.clear_results()
    x,y,z,w = symath.symbols('x y z w')
    exp1 = x(y, z, w, w, x)
    exp2 = x(w, z, w, y)
    print ''
    print 'edit_distance(%s, %s) = %d' % (exp1, exp2, ed.edit_distance(exp1, exp2))
    rv = ed._tuple_edit_distance.results
    #util.pretty(rv)

    m = zeros([len(exp1), len(exp2)], dtype=int)
    for i in range(len(exp1)):
      for j in range(len(exp2)):
        m[i,j] = -1

    for k in rv:
      m[len(k[0][0]), len(k[0][1])] = rv[k][0]
    print m

if __name__ == '__main__':
  unittest.main()
