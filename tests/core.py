#!/usr/bin/env python

import unittest
import symath

class TestCoreClasses(unittest.TestCase):
  def setUp(self):
    self.x, self.y = symath.symbols('x y')

  def test_identity(self):
    self.assertEqual(self.x * 1, self.x)
    self.assertEqual(self.x + 0, self.x)

  def test_zero(self):
    self.assertEqual(self.x * 0, 0)

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

  def test_nonsymbol_function_head(self):
    h = self.x + self.y
    self.assertEqual(h(self.x), (self.x + self.y)(self.x))

  def test_nonsymbol_function_head_complete(self):
    self.assertEqual(str((self.x + self.y)(self.x + self.y)), '(x + y)((x + y))')

  def test_pow(self):
    self.assertEqual(self.x * self.x, self.x ** 2)
    self.assertEqual(self.x ** 2 * self.x, self.x ** 3)
    self.assertEqual(self.x * self.x * self.x, self.x ** 3)
    self.assertEqual((2 * self.x) * self.x, self.x ** 2 * 2)

  def test_fold_additions(self):
    self.assertEqual(self.x + self.x, 2 * self.x)
    self.assertEqual(self.x + self.y * self.x, (self.y + 1) * self.x)

  def test_equality(self):
    self.assertNotEqual(self.x(3), self.x(4))
    self.assertEqual(self.x, self.x)
    self.assertEqual(self.x(3), self.x(3))
    self.assertEqual(self.x(self.y), self.x(self.y))

  def test_subtractions(self):
    self.assertEqual(self.x - self.y, self.x + (-self.y))

  def test_addition_reorder(self):
    self.assertEqual(self.x + self.y * self.y + self.x, self.x + self.x + self.y * self.y)

  def test_numeric_ops(self):
    self.assertEqual((self.x + self.y).substitute({self.x: 3, self.y: 4}), 7)

  def test_failure_case_1(self):
    self.assertEqual(self.y + self.x * self.y + self.x, self.x + self.y + self.x * self.y)

  def test_logical_operands(self):
    t = symath.symbolic(True)
    f = symath.symbolic(False)

    self.assertEqual(symath.stdops.LogicalAnd(t, f), f)
    self.assertEqual(symath.stdops.LogicalAnd(t, f), False)
    self.assertEqual(symath.stdops.LogicalOr(t, f), t)
    self.assertEqual(symath.stdops.LogicalOr(t, f), True)
    self.assertEqual(symath.stdops.LogicalXor(t, t), False)
    self.assertEqual(symath.stdops.LogicalXor(f, t), True)
    self.assertEqual(symath.stdops.LogicalXor(f, f), False)

  def test_wilds_equality(self):
    self.assertEqual(symath.wild('a'), symath.wild('a'))
    self.assertNotEqual(symath.wild('a'), symath.wild('b'))
    self.assertNotEqual(symath.wild(), symath.wild())

  def test_hash(self):
    a = self.x(4, self.y + 4)
    b = self.x(4, self.y + 4)
    self.assertEqual(hash(a), hash(b))

if __name__ == '__main__':
  unittest.main()
