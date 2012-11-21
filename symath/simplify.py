#!/usr/bin/env python
import threading
import stdops as stdops
import core
import copy
import operator

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
    exp = Fn(exp.fn, *args)

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
  if exp[0].name == '-' and len(exp) == 3:
    return exp[1] + (-exp[2])
  return exp

def _strip_identities_pass(exp):
  if len(exp) == 3:
    kargs = exp[0].kargs
    lidentity = kargs['lidentity'] if 'lidentity' in kargs else kargs['identity'] if 'identity' in kargs else None
    ridentity = kargs['ridentity'] if 'ridentity' in kargs else kargs['identity'] if 'identity' in kargs else None

    if lidentity != None and exp[1] == lidentity:
      return exp[2].walk(_strip_identities)
    if ridentity != None and exp[2] == ridentity:
      return exp[1].walk(_strip_identities)

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
    rv = exp
    if len(rv) == 3 and rv[0] == op1:
      if rv[1][0] == op2 and len(rv[1]) == 3:
        rv = op2(op1(rv[1][1], rv[2]), op1(rv[1][2], rv[2]))
    if len(rv) == 3 and rv[0] == op1:
      if rv[2][0] == op2 and len(rv[2]) == 3:
        rv = op2(op1(rv[2][1], rv[1]), op1(rv[2][2], rv[1]))

    return rv
  return _

def _simplify_known_values(exp):
  if len(exp) > 1 and 'numeric' in exp[0].kargs:
    args = []
    for i in range(1, len(exp)):
      if not isinstance(exp[i], core._KnownValue):
        return exp
      if 'cast' in exp[0].kargs:
        args.append(exp[0].kargs['cast'](exp[i].value()))
      else:
        args.append(exp[i].value())

    nfn = getattr(operator, exp[0].kargs['numeric'])
    return core.symbolic(nfn(*args))
  else:
    return exp

def _get_factors(exp):
  rv = {}
  if exp[0] == stdops.Mul and len(exp) == 3:
    tmp = _get_factors(exp[1])
    for i in tmp:
      if i in rv:
        rv[i] += tmp[i] 
      else:
        rv[i] = tmp[i]
    tmp = _get_factors(exp[2])
    for i in tmp:
      if i in rv:
        rv[i] += tmp[i] 
      else:
        rv[i] = tmp[i]
  elif exp[0] == stdops.Pow and len(exp) == 3:
    rv = _get_factors(exp[1])
    for k in rv:
      rv[k] = rv[k] * exp[2]
  else:
    rv[exp] = 1

  return rv

def _fold_additions(exp):
  if exp[0] == stdops.Add and len(exp) == 3:
    if exp[1] == exp[2]:
      exp = exp[1] * 2

    if exp[1][0] == stdops.Mul and len(exp[1]) == 3:
      if exp[1][1] == exp[2]:
        exp = (exp[1][2] + 1) * exp[2]
      if exp[1][2] == exp[2]:
        exp = (exp[1][1] + 1) * exp[2]

    if exp[2][0] == stdops.Mul and len(exp[2]) == 3:
      try:
        if exp[2][1] == exp[1]:
          exp = (exp[2][2] + 1) * exp[1]
        elif exp[2][2] == exp[1]:
          exp = (exp[2][1] + 1) * exp[1]
      except:
        print 'FOLD ADDITIONS: wtf.. %s [%d] %s [%d]' % (exp[1], len(exp[1]), exp[2], len(exp[2]))

  return exp

def _convert_to_pow(exp):
  if len(exp) != 3:
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
    _strip_identities \
    )

  return exp.walk(_strip_identities)

# FIXME/TODO:
#  using a lock for this is super retarded, but it's a quick easy hack
#  the problem is that we don't want expressions being created by simplify to
#  trigger a simplification themselves
_simplify_lock = threading.RLock()
_in_simplify = False

def simplify(exp):
  '''
  attempts to simplify an expression
  is knowledgeable of the operations defined in symath.stdops
  '''
  global _in_simplify
  global _simplify_lock

  with _simplify_lock:
    if _in_simplify:
      return exp
  
    _in_simplify = True
    sexp = _simplify_pass(exp)
    while sexp != exp:
      #print '%s => %s' % (exp, sexp)
      exp = sexp
      sexp = _simplify_pass(exp)
  
    _in_simplify = False
    return exp

