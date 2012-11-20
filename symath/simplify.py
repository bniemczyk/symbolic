#!/usr/bin/env python
import threading
import stdops as stdops

def _remove_subtractions(exp):
  if exp[0].name == '-' and len(exp) == 3:
    return exp[1] + (-exp[2])
  return exp

def _strip_identities(exp):
  if len(exp) == 3:
    kargs = exp[0].kargs
    lidentity = kargs['lidentity'] if 'lidentity' in kargs else kargs['identity'] if 'identity' in kargs else None
    ridentity = kargs['ridentity'] if 'ridentity' in kargs else kargs['identity'] if 'identity' in kargs else None

    if lidentity != None and exp[1] == lidentity:
      return exp[2].walk(_strip_identities)
    if ridentity != None and exp[2] == ridentity:
      return exp[1].walk(_strip_identities)

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
      if exp[2][1] == exp[1]:
        exp = (exp[2][2] + 1) * exp[1]
      if exp[2][2] == exp[1]:
        exp = (exp[2][1] + 1) * exp[1]

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

def _simplify_pass(exp):
  exp = exp.walk(\
    _strip_identities, \
    _remove_subtractions, \
    _strip_identities, \
    _distribute(stdops.BitAnd, stdops.BitOr), \
    _strip_identities, \
    _distribute(stdops.Mul, stdops.Add), \
    _strip_identities, \
    _convert_to_pow, \
    _strip_identities, \
    _fold_additions, \
    _strip_identities
    )

  return exp

# FIXME/TODO:
#  using a lock for this is super retarded, but it's a quick easy hack
#  the problem is that we don't want expressions being created by simplify to
#  trigger a simplification themselves
_simplify_lock = threading.RLock()
_in_simplify = False

def simplify(exp):
  global _in_simplify
  global _simplify_lock

  with _simplify_lock:
    if _in_simplify:
      return exp
  
    _in_simplify = True
    sexp = _simplify_pass(exp)
    while sexp != exp:
      exp = sexp
      sexp = _simplify_pass(exp)
  
    _in_simplify = False
    return exp

