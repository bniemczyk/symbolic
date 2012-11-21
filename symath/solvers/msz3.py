#!/usr/bin/env python
import z3
import symath

def _convert(exp):
  a,b = symath.wilds('a b')
  vals = symath.WildResults()

  if exp.match(a < b, vals):
    return _convert(vals.a) < _convert(vals.b)
  elif exp.match(a > b, vals):
    return _convert(vals.a) > _convert(vals.b)
  elif exp.match(symath.stdops.Equal(a, b), vals):
    return _convert(vals.a) == _convert(vals.b)
  elif exp.match(a <= b, vals):
    return _cnvert(vals.a) <= _convert(vals.b)
  elif exp.match(a >= b, vals):
    return _convert(vals.a) >= _convert(vals.b)
  elif exp.match(a + b, vals):
    return _convert(vals.a) + _convert(vals.b)
  elif exp.match(a - b, vals):
    return _convert(vals.a) - _convert(vals.b)
  elif exp.match(a * b, vals):
    return _convert(vals.a) * _convert(vals.b)
  elif exp.match(a / b, vals):
    return _convert(vals.a) / _convert(vals.b)
  elif exp.match(a ^ b, vals):
    return _convert(vals.a) ^ _convert(vals.b)
  elif exp.match(a & b, vals):
    return _convert(vals.a) & _convert(vals.b)
  elif exp.match(a | b, vals):
    return _convert(vals.a) | _convert(vals.b)
  elif exp.match(a ** b, vals):
    return _convert(vals.a) ** _convert(vals.b)
  elif exp.match(symath.stdops.LogicalAnd(a, b), vals):
    return z3.And(_convert(vals.a), _convert(vals.b))
  elif exp.match(symath.stdops.LogicalOr(a, b), vals):
    return z3.Or(_convert(vals.a), _convert(vals.b))
  elif exp.match(symath.stdops.LogicalXor(a, b), vals):
    return z3.Or(z3.And(_convert(vals.a), z3.Not(_convert(vals.b))), z3.And(_convert(vals.b), z3.Not(_convert(vals.a))))
  elif isinstance(exp, symath.Symbol) and exp.is_integer:
    return z3.Int(exp.name)
  elif isinstance(exp, symath.Symbol) and exp.is_bool:
    return z3.Bool(exp.name)
  elif isinstance(exp, symath.Symbol) and exp.is_bitvector > 0:
    return z3.BitVec(exp.name, exp.is_bitvector)
  elif isinstance(exp, symath.Symbol):
    return z3.Real(exp.name)
  elif isinstance(exp, symath.core._KnownValue):
    return exp.value()
  else:
    raise BaseException("Invalid argument (%s) (type: %s) passed to z3 solver" % (exp, type(exp)))

class Result(object):

  def __init__(self, model):
    self.model = model

  def __getitem__(self, idx):
    return self.model[_convert(symath.symbolic(idx))]

  def __getattr__(self, idx):
    return self[idx]

class ConstraintSet(set):

  def __init__(self):
    super(ConstraintSet, self).__init__()

  def solve(self):
    a,b = symath.wilds('a b')

    solver = z3.Solver()
    for i in self:
      if \
          i.match(symath.stdops.LogicalAnd(a, b)) or \
          i.match(symath.stdops.LogicalOr(a, b)) or \
          i.match(symath.stdops.LogicalXor(a, b)) or \
          i.match(symath.stdops.Equal(a, b)) or \
          i.match(a < b) or \
          i.match(a > b) or \
          i.match(a <= b) or \
          i.match(a >= b) or \
          i.match(a <= b):
        solver.add(_convert(i))
      else:
        solver.add(_convert(i) == 0)
    if solver.check() != z3.sat:
      return None

    return Result(solver.model())
