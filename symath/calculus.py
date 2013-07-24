from core import WildResults, wilds, symbolic, symbols
from functions import *
from stdops import *
from memoize import Memoize

_known_functions = (Add, Sub, Mul, Div, Pow, Sin, Cos, Tan, Exp)

class DifferentiationError(Exception):
  pass

def _diff_known_function(expression, variable):

  vals = WildResults()
  g,h = wilds('g h')

  if expression[0] not in _known_functions:
    raise DifferentiationError("d/d%s  %s" % (variable,expression))

  if expression.match(g + h, vals):
    return diff(vals.g, variable) + diff(vals.h, variable)

  elif expression.match(g - h, vals):
    return diff(vals.g, variable) - diff(vals.h, variable)

  elif expression.match(variable ** g, vals) and vals.g.is_integer:
    return vals.g * (variable ** (vals.g - 1))

  elif expression.match(g * h, vals):
    return vals.g * diff(vals.h, variable) + vals.h * diff(vals.g, variable)

  elif expression.match(g / h, vals):
    return (diff(vals.g, variable) * vals.h - vals.g * diff(vals.h, variable)) / (vals.h ** 2)

  elif expression.match(Exp(variable)):
    return expression

  elif expression.match(Sin(variable)):
    return Sin(variable)

  elif expression.match(Cos(variable)):
    return -1 * Sin(variable)

  raise DifferentiationError("d/d%s  %s" % (variable,expression))

def diff(expression, variable):

  vals = WildResults()
  f,a,b = wilds('f a b')

  expression = expression.simplify()

  if variable not in expression:
    return symbolic(0)

  elif expression.match(variable):
    return symbolic(1)

  elif expression.match(f(a,b), vals) and vals.f in _known_functions:
    return _diff_known_function(expression, variable)

  elif expression.match(f(a), vals) and vals.f in _known_functions:
    return _diff_known_function(vals.f(vals.a), vals.a) * diff(vals.a, variable)

  raise DifferentiationError("d/d%s  %s" % (variable,expression))

