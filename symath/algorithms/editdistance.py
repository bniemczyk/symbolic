#!/usr/bin/env

'''
Edit distance between 2 expressions, this is inspired by levenshtein edit distance
uses match to calculate equality, so you can use one with wilds if you want complex
rules
'''

import symath
import symath.util as util

def _combine_subs(subs, vals):
  rv = {}

  for k in subs:
    assert not isinstance(subs[k], symath.core.Wild)
    rv[k] = subs[k]

  for k in vals:
    assert not isinstance(vals[k], symath.core.Wild)
    assert k not in rv
    rv[k] = vals[k]

  return rv

@symath.memoize.Memoize
def _recursive_len(exp):
  if isinstance(exp, symath.core.Fn):
    rv = 1
    for i in exp.args:
      rv += _recursive_len(i)
    return rv
  else:
    return len(exp)

@symath.memoize.Memoize
def _tuple_edit_distance(exp1, exp2, **subs):
  '''
  takes 2 tuples of expressions
  '''

  if len(exp1) == 0:
    return _recursive_len(exp2),subs
  elif len(exp2) == 0:
    return _recursive_len(exp1),subs

  # insert
  d,ns = _tuple_edit_distance(exp1[1:], exp2, **subs)
  rv = d+1, ns

  # remove
  d,ns = _tuple_edit_distance(exp1, exp2[1:], **subs)
  if d+1 < rv[0]:
    rv = d+1, ns

  # substitution or continuation
  d,ns = _edit_distance(exp1[0], exp2[0], **subs)
  d2,ns = _tuple_edit_distance(exp1[1:], exp2[1:], **ns)
  if d+d2 < rv[0]:
    rv = d+d2, ns

  return rv

@symath.memoize.Memoize
def _edit_distance(exp1, exp2, **subs):
  vals = symath.core.WildResults()

  csubs = {}
  for k in subs:
    csubs[symath.core.wild(k)] = subs[k]

  exp1 = exp1.substitute(csubs)
  exp2 = exp2.substitute(csubs)

  if exp1.match(exp2, vals) or exp2.match(exp1, vals):
    return 0, _combine_subs(subs, vals)

  elif isinstance(exp1, symath.core.Fn) and isinstance(exp2, symath.core.Fn):
    d,ns = _edit_distance(exp1[0], exp2[0], **subs)
    e,ns = _tuple_edit_distance(exp1.args, exp2.args, **ns)
    return d + e, ns

  elif isinstance(exp1, symath.core.Fn) and not isinstance(exp2, symath.core.Fn):
    d,ns = _edit_distance(exp1[0], exp2, **subs)
    e,ns = _tuple_edit_distance((), exp1.args, **ns)
    return d + e, ns

  elif isinstance(exp2, symath.core.Fn) and not isinstance(exp1, symath.core.Fn):
    d,ns = _edit_distance(exp2[0], exp1, **subs)
    e,ns = _tuple_edit_distance((), exp2.args, **ns)
    return d + e, ns

  else:
    return 1, subs

@symath.memoize.Memoize
def _prepare_exps(exp1, exp2):
  '''
  replace wilds with their equivelant symbols in exp2
  because otherwise our .substitute() cals will just replace
  wilds with wilds, which is totally useless
  '''
  if util.has_wilds(exp1) and util.has_wilds(exp2):
    def _(exp):
      if isinstance(exp, symath.core.Wild):
        return symath.symbolic(exp.name)
      else:
        return exp
  
    old_exp2 = exp2
    exp2 = exp2.walk(_)
    assert old_exp2 != exp2

  return exp1,exp2


def edit_distance(exp1, exp2):
  '''
  takes 2 expressions and returns a distance metric
    heavily inspired by levenshtien distance between strings

  this is primarily useful so that you can make 'fuzzy signatures' out of symbolic
  expressions
  '''
  exp1,exp2 = _prepare_exps(exp1, exp2)
  return _edit_distance(exp1, exp2)[0]

def edit_substitutions(exp1, exp2):
  '''
  takes 2 expressions and returns the wild substitutions required to find the minimum distance
  '''
  exp1,exp2 = _prepare_exps(exp1, exp2)
  return _edit_distance(exp1, exp2)[1]
