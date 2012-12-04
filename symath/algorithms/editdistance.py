#!/usr/bin/env

'''
Edit distance between 2 expressions, this is inspired by levenshtein edit distance
uses match to calculate equality, so you can use one with wilds if you want complex
rules
'''

import symath

@symath.memoize.Memoize
def _recursive_len(exp):
  if isinstance(exp, symath.core.Fn):
    rv = 1
    for i in exp.args:
      rv += _recursive_len(i)
    return rv
  else:
    return 1

@symath.memoize.Memoize
def _edit_distance(exp1, exp2):
  '''
  takes 2 tuples of expressions
  '''

  if len(exp1) == 0:
    return _recursive_len(exp2)
  elif len(exp2) == 0:
    return _recursive_len(exp1)

  cases = [
    _edit_distance(exp1[1:], exp2), # insertion 
    _edit_distance(exp1, exp2[1:]), # removal
    _edit_distance(exp1[1:], exp2[1:]) + edit_distance(exp1[0], exp2[0]) # substitution or continuation
    ]

  return min(cases)

@symath.memoize.Memoize
def edit_distance(exp1, exp2):
  '''
  takes 2 expressions and returns a distance metric
    heavily inspired by levenshtien distance between strings

  this is primarily useful so that you can make 'fuzzy signatures' out of symbolic
  expressions
  '''

  if exp1.match(exp2) or exp2.match(exp1):
    return 0

  elif isinstance(exp1, symath.core.Fn) and isinstance(exp2, symath.core.Fn):
    return edit_distance(exp1[0], exp2[0]) + _edit_distance(exp1.args, exp2.args)

  elif isinstance(exp1, symath.core.Fn) and not isinstance(exp2, symath.core.Fn):
    return edit_distance(exp1[0], exp2) + _edit_distance((), exp1.args)

  elif isinstance(exp2, symath.core.Fn) and not isinstance(exp1, symath.core.Fn):
    return edit_distance(exp2[0], exp1) + _edit_distance((), exp2.args)

  else:
    return 1
