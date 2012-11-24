#!/usr/bin/env python
import threading
import stdops as stdops
import core
import copy
import operator
import factor

from core import wild

def _order(a,b):
  '''
  used internally to put shit in canonical order
  '''
  if isinstance(a, core.Number):
    if(isinstance(b, core.Number)):
      return -1 if a.n < b.n else (0 if a.n == b.n else 1)
    return -1
  elif isinstance(b, core.Number):
    return 1
  elif isinstance(a, core.Symbol):
    if(isinstance(b, core.Symbol)):
      return -1 if a.name < b.name else (0 if a.name == b.name else 1)
    return -1
  elif isinstance(b, core.Symbol):
    return 1

  else:
    return -1 if str(a) < str(b) else (0 if str(a) == str(b) else 1)

def _assoc_reorder(exp):
  if len(exp) == 1:
    return exp

  # canonicalize the arguments first
  args = list(map(lambda x: _assoc_reorder(x), exp.args))
  if tuple(args) != tuple(exp.args):
    exp = core.Fn(exp.fn, *args)

  # if it's associative and one of the arguments is another instance of the
  # same function, canonicalize the order
  if len(exp.args) == 2 and 'associative' in exp.kargs and exp.kargs['associative']:
    args = exp._get_assoc_arguments()
    oldargs = tuple(args)
    args.sort(_order)
    if tuple(args) != oldargs:
      kargs = copy.copy(exp.kargs)
      exp = reduce(lambda a, b: exp.fn(a,b), args)

  return exp

def _remove_subtractions(exp):
  a,b = core.wilds('a b')
  vals = {}
  if exp.match(stdops.Sub(a,b), vals):
    return vals['a'] + (-vals['b'])
  else:
    return exp

def _strip_identities_pass(exp):
  a,b,c = core.wilds('a b c')
  vals = {}

  if exp.match(a(b, c)):
    kargs = exp[0].kargs
    lidentity = kargs['lidentity'] if 'lidentity' in kargs else kargs['identity'] if 'identity' in kargs else None
    ridentity = kargs['ridentity'] if 'ridentity' in kargs else kargs['identity'] if 'identity' in kargs else None
    
    if lidentity != None and exp.match(a(lidentity, b), vals):
      return vals['b'].walk(_strip_identities)
    elif ridentity != None and exp.match(a(b, ridentity), vals):
      return vals['b'].walk(_strip_identities)

  return exp

def _strip_identities(exp):
  rv = exp.walk(_strip_identities_pass)
  while rv != exp:
    exp = rv
    rv = exp.walk(_strip_identities_pass)

  return rv

def _zero_terms(exp):
  if hasattr(exp[0],'kargs') and 'zero' in exp[0].kargs:
    for i in range(1, len(exp)):
      if exp[1] == exp[0].kargs['zero'] or exp[2] == exp[0].kargs['zero']:
        return exp[0].kargs['zero']
  return exp

def _distribute(op1, op2):
  def _(exp):
    a,b,c = core.wilds('a b c')
    vals = {}

    if exp.match(op1(op2(a, b), c), vals):
      return op2(op1(vals['c'], vals['a']), op1(vals['c'], vals['b']))
    elif exp.match(op1(a, op2(b, c)), vals):
      return op2(op1(vals['a'], vals['b']), op1(vals['a'], vals['c']))
    else:
      return exp

  return _

def _simplify_mul_div(exp):
  a,b,c = core.wilds('a b c')
  vals = core.WildResults()

  if exp.match(c * (b / c), vals) or exp.match((b / c) * c, vals):
    return vals.b

  if exp.match(a * (b / c), vals) or exp.match((b / c) * a, vals):
    return (vals.a * vals.b) / vals.c

  elif exp.match(a / b, vals) and isinstance(vals.b, core.Number):
    return vals.a * (1.0 / vals.b.value())

  elif exp.match(a / b, vals) and factor.is_factor(vals.b, vals.a):
    return factor.get_coefficient(vals.a, vals.b)

  return exp

def _simplify_known_values(exp):
  a,b,c = core.wilds('a b c')
  vals = {}
  if exp.match(a(b,c), vals) \
      and 'numeric' in vals['a'].kargs \
      and isinstance(vals['b'], core._KnownValue) \
      and isinstance(vals['c'], core._KnownValue):
    cast = vals['a'].kargs['cast'] if 'cast' in vals['a'].kargs else (lambda x: x)
    nfn = getattr(operator, vals['a'].kargs['numeric'])
    return core.symbolic(nfn(cast(vals['b'].value()), cast(vals['c'].value())))
  else:
    return exp

def _get_factors(exp):
  rv = {}
  a,b = core.wilds('a b')
  vals = {}

  if exp.match(a * b, vals):
    tmp = _get_factors(vals['a'])
    for i in tmp:
      if i in rv:
        rv[i] += tmp[i] 
      else:
        rv[i] = tmp[i]
    tmp = _get_factors(vals['b'])
    for i in tmp:
      if i in rv:
        rv[i] += tmp[i] 
      else:
        rv[i] = tmp[i]
  elif exp.match(a ** b, vals):
    rv = _get_factors(vals['a'])
    for k in rv:
      rv[k] = rv[k] * vals['b']
  else:
    rv[exp] = 1

  return rv

def _fold_additions(exp):
  a,b,c = core.wilds('a b c')
  vals = {}

  if exp.match(a + a, vals):
    return vals['a'] * 2

  elif exp.match(a + (a * b), vals) or exp.match(a + (b * a), vals):
    return (vals['b'] + 1) * vals['a']

  else:
    return exp

def _convert_to_pow(exp):
  a,b,c = core.wilds('a b c')

  if not exp.match(a(b,c)):
    return exp

  fs = _get_factors(exp)
  rv = 1
  for k in fs:
    if fs[k] == 1:
      rv = rv * k
    else:
      rv = rv * (k ** fs[k])
  return rv

def _args(exp):
  return list(map(lambda x: exp[x], range(1, len(exp))))

def _simplify_bitops(exp):
  a,b = core.wilds('a b')
  vals = core.WildResults()

  if exp.match(a ^ a):
    return core.symbolic(0)
  elif exp.match(a | a, vals):
    return vals.a
  elif exp.match(a & a, vals):
    return vals.a
  elif exp.match((a << b) >> b, vals) or exp.match((a >> b) << b, vals):
    return vals.a
  else:
    return exp

def _commutative_reorder(exp):
  oexp = exp
  if len(exp) > 1 and 'commutative' in exp[0].kargs:
    args = list(map(lambda x: x.walk(_commutative_reorder), _args(exp)))
    args.sort(cmp=_order)
    exp = exp[0](*args)
  return exp

def _simplify_pass(exp):
  exp = exp.walk(\
    _commutative_reorder, \
    _strip_identities, \
    _simplify_mul_div, \
    _strip_identities, \
    _simplify_known_values, \
    _strip_identities, \
    _convert_to_pow, \
    _strip_identities, \
    _remove_subtractions, \
    _strip_identities, \
    _distribute(stdops.BitAnd, stdops.BitOr), \
    _strip_identities, \
    _distribute(stdops.Mul, stdops.Add), \
    _strip_identities, \
    _fold_additions, \
    _strip_identities, \
    _zero_terms, \
    _strip_identities, \
    _commutative_reorder, \
    _strip_identities, \
    _distribute(stdops.BitAnd, stdops.BitOr), \
    _strip_identities, \
    _distribute(stdops.Mul, stdops.Add), \
    _strip_identities, \
    _assoc_reorder, \
    _strip_identities, \
    _simplify_bitops, \
    _strip_identities, \
    _simplify_mul_div, \
    _strip_identities \
    )

  return exp.walk(_strip_identities)

def simplify(exp):
  '''
  attempts to simplify an expression
  is knowledgeable of the operations defined in symath.stdops
  '''
  sexp = _simplify_pass(exp)
  while sexp != exp:
    #print '%s => %s' % (exp, sexp)
    exp = sexp
    sexp = _simplify_pass(exp)

  return exp
