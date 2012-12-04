#!/usr/bin/env python

import unittest
import symath

class TestCoreClasses(unittest.TestCase):
  def setUp(self):
    self.x, self.y, self.z = symath.symbols('x y z')

  def test_identity(self):
    self.assertEqual((self.x * 1).simplify(), (self.x).simplify())
    self.assertEqual((self.x + 0).simplify(), (self.x).simplify())

  def test_zero(self):
    self.assertEqual((self.x * 0).simplify(), 0)

  def test_index(self):
    self.assertEqual(len(self.x), 1)
    self.assertEqual(self.x[0], self.x)

    exp = self.x + self.y * 3
    self.assertEqual(len(exp), 3)
    self.assertEqual(exp[0].name, '+')

  def test_substitute(self):
    exp = self.x + self.y * 3
    exp = exp.substitute({self.x: 3, self.y: 4})
    self.assertEqual(exp.simplify(), 15)

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
    self.assertEqual((self.x * self.x).simplify(), (self.x ** 2).simplify())
    self.assertEqual((self.x ** 2 * self.x).simplify(), (self.x ** 3).simplify())
    self.assertEqual((self.x * self.x * self.x).simplify(), (self.x ** 3).simplify())
    self.assertEqual(((2 * self.x) * self.x).simplify(), (self.x ** 2 * 2).simplify())

  def test_fold_additions(self):
    self.assertEqual((self.x + self.x).simplify(), (2 * self.x).simplify())
    self.assertEqual((self.x + self.y * self.x).simplify(), ((self.y + 1) * self.x).simplify())

  def test_equality(self):
    self.assertNotEqual(self.x(3), self.x(4))
    self.assertEqual((self.x).simplify(), (self.x).simplify())
    self.assertEqual((self.x(3)).simplify(), (self.x(3)).simplify())
    self.assertEqual((self.x(self.y)).simplify(), (self.x(self.y)).simplify())

  def test_subtractions(self):
    self.assertEqual((self.x - self.y).simplify(), (self.x + (-self.y)).simplify())

  def test_addition_reorder(self):
    self.assertEqual((self.x + self.y * self.y + self.x).simplify(), (self.x + self.x + self.y * self.y).simplify())

  def test_numeric_ops(self):
    self.assertEqual((self.x + self.y).substitute({self.x: 3, self.y: 4}).simplify(), 7)

  def test_mul_div(self):
    self.assertEqual((self.x * (self.z / self.y)).simplify(), ((self.x * self.z) / self.y).simplify())
    self.assertEqual((((3 + self.x) / (2 + self.x)) * (2 + self.x)).simplify(), (3 + self.x).simplify())

  def test_divide_by_factor(self):
    self.assertEqual(((self.x * self.y) / self.y).simplify(), self.x)

  def test_divide_by_factor(self):
    self.assertEqual(((self.x * self.y) / self.y).simplify(), self.x)

  def test_failure_case_1(self):
    self.assertEqual((self.y + self.x * self.y + self.x).simplify(), (self.x + self.y + self.x * self.y).simplify())

  def test_logical_operands(self):
    t = symath.symbolic(True)
    f = symath.symbolic(False)

    self.assertEqual(symath.stdops.LogicalAnd(t, f).simplify(), f)
    self.assertEqual(symath.stdops.LogicalAnd(t, f).simplify(), False)
    self.assertEqual(symath.stdops.LogicalOr(t, f).simplify(), t)
    self.assertEqual(symath.stdops.LogicalOr(t, f).simplify(), True)
    self.assertEqual(symath.stdops.LogicalXor(t, t).simplify(), False)
    self.assertEqual(symath.stdops.LogicalXor(f, t).simplify(), True)
    self.assertEqual(symath.stdops.LogicalXor(f, f).simplify(), False)

  def test_wilds_equality(self):
    self.assertEqual(symath.wild('a'), symath.wild('a'))
    self.assertNotEqual(symath.wild('a'), symath.wild('b'))
    self.assertNotEqual(symath.wild(), symath.wild())

  def test_hash(self):
    a = self.x(4, self.y + 4)
    b = self.x(4, self.y + 4)
    self.assertEqual(hash(a), hash(b))

  def test_simplify_bitops(self):
    self.assertEqual((self.x ^ self.x).simplify(), 0)
    self.assertEqual((self.x & self.x).simplify(), (self.x).simplify())
    self.assertEqual((self.x | self.x).simplify(), (self.x).simplify())
    self.assertEqual(((self.x << 8) >> 8).simplify(), (self.x).simplify())

  def test_edit_distance(self):
    from symath.algorithms.editdistance import edit_distance
    self.assertEqual(edit_distance(self.x(self.x, self.y, self.x), self.y(self.x, self.x, self.x)), 2)
    self.assertEqual(edit_distance(self.x(self.y, self.x), self.x(self.y, self.y, self.x)), 1)
    self.assertEqual(edit_distance(self.x(self.y, self.x), self.x(self.x)), 1)
    self.assertEqual(edit_distance(self.x(self.y, self.y, self.x), self.x(self.x)), 2)

if __name__ == '__main__':
  unittest.main()
