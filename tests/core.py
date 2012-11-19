#!/usr/bin/env python

import unittest
import symath

class TestCoreClasses(unittest.TestCase):
  def setUp(self):
    self.x, self.y = symath.symbols('x y')

  def test_index(self):
    self.assertEqual(len(self.x), 1)
    self.assertEqual(self.x[0], self.x)

    exp = self.x + self.y * 3
    self.assertEqual(len(exp), 3)
    self.assertEqual(exp[0].name, '+')

  def test_substitute(self):
    exp = self.x + self.y * 3
    exp = exp.substitute({self.x: 3, self.y: 4})
    self.assertEqual(exp, 15)

  def test_symath_imports_symbolic(self):
    sn = symath.symbolic(3)
    self.assertTrue(isinstance(sn, symath.Number))
    self.assertEqual(sn, 3)

if __name__ == '__main__':
  unittest.main()
