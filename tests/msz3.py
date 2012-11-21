#!/usr/bin/env python

import symath
import symath.solvers as solvers
import unittest

class TestZ3(unittest.TestCase):

  def setUp(self):
    self.x, self.y = symath.symbols('x y')

  def test_basic_solver(self):
    cs = solvers.z3.ConstraintSet()
    cs.add(symath.stdops.Equal(self.x ** 2, 4))
    rv = cs.solve()
    self.assertNotEqual(rv, None)
    self.assertEqual(rv.x, 2)


if __name__ == '__main__':
  unittest.main()
