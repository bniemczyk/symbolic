#!/usr/bin/env

'''
Edit distance between 2 expressions, this is inspired by levenshtein edit distance
uses match to calculate equality, so you can use one with wilds if you want complex
rules
'''

import symath
import symath.util as util
import numpy

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

def _tuple_edit_distance(t1, t2, k, **subs):
  
  '''
  Build a matrix of edit distances for prefixes, 
  using dp techniques but recognizes that diagnols are
  monotonically increasing, so we can skip calculating
  a bunch of crap, return the bottom right corner of the matrix and the subs made

  here are some examples comparing two strings (notice all changes are +1,
  in reality we use +edit_distance because our elements can have a distance
  > 1

  k == 4

         a    b    c    d    e    f
    0    1    2    3    4    5    6
  g 1    1    2    3    4
  h 2                       >=4
  i 3                            >=4

  k == 3
         a    b    c    d    e
    0    1    2    3    4    5
  b 1         1   >=1
  b 2        >=1   2
  c 3                   2
  e 4                        2
  '''

  M = numpy.ndarray((len(t1)+1, len(t2)+1), int)
  M.fill(-1)
  M[0,0] = 0

  for i in range(1, len(t1)+1):
    M[i,0] = _recursive_len(t1[i-1]) + M[i-1,0]

  for i in range(1, len(t2)+1):
    M[0,i] = _recursive_len(t2[i-1]) + M[0,i-1]

  @symath.memoize.Memoize
  def _get_val(x,y,k,**subs):
    if M[x,y] != -1:
      return M[x,y], subs

    # we always need the diagonal and we want to calculate those first
    d, subs = _get_val(x-1,y-1,k, **subs)

    # diagonals are always increasing, so we may be able to bug out here
    if d >= k:
      return d, subs

    # now we need the edit distance of these particular members
    (ed, subs) = _edit_distance(t1[x-1],t2[y-1],k - d, **subs)
    
    # we can never have a result smaller than the previous entry in the diagonal
    if ed == 0:
      M[x,y] = d
      return d, subs

    # we only care about decx and decy if they can be less than the (d + ed - len)
    # because otherwise the diagonal will always be better
    rlen = _recursive_len(t2[y-1])
    decx,subs = _get_val(x-1, y, d + ed - rlen)
    decy,subs = _get_val(x, y - 1, d + ed - rlen)

    M[x,y] = min([decx + rlen, decy + rlen, d + ed])
    return M[x,y], subs

  rv = _get_val(len(t1), len(t2), k, **subs)
  if util.DEBUG:
    util.debug('\nEDIT(%s, %s) = %d' % (t1,t2, rv[0]))
    util.debug(M)
    util.debug('skipped %d out of %d calculations' % (len(filter(lambda x: x == -1, M.flatten())), ((len(t1) + 1) * (len(t2) + 1)) - len(t1) - len(t2) - 1))
  return rv

@symath.memoize.Memoize
def _edit_distance(exp1, exp2, k, **subs):
  assert isinstance(k, int)
  vals = symath.core.WildResults()

  csubs = {}
  for key in subs:
    csubs[symath.core.wild(key)] = subs[key]

  exp1 = exp1.substitute(csubs)
  exp2 = exp2.substitute(csubs)

  if exp1.match(exp2, vals) or exp2.match(exp1, vals):
    return 0, _combine_subs(subs, vals)

  elif isinstance(exp1, symath.core.Fn) and isinstance(exp2, symath.core.Fn):
    d,ns = _edit_distance(exp1[0], exp2[0], k, **subs)
    e,ns = _tuple_edit_distance(exp1.args, exp2.args, k - d, **ns)
    return d + e, ns

  elif isinstance(exp1, symath.core.Fn) and not isinstance(exp2, symath.core.Fn):
    d,ns = _edit_distance(exp1[0], exp2, k, **subs)
    e,ns = _tuple_edit_distance((), exp1.args, k - d, **ns)
    return d + e, ns

  elif isinstance(exp2, symath.core.Fn) and not isinstance(exp1, symath.core.Fn):
    d,ns = _edit_distance(exp2[0], exp1, k, **subs)
    e,ns = _tuple_edit_distance((), exp2.args, k - d, **ns)
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


def edit_distance(exp1, exp2, k=None):
  '''
  takes 2 expressions and returns a distance metric
    heavily inspired by levenshtien distance between strings

  this is primarily useful so that you can make 'fuzzy signatures' out of symbolic
  expressions
  '''
  if k == None:
    k = max([_recursive_len(exp1), _recursive_len(exp2)])

  exp1,exp2 = _prepare_exps(exp1, exp2)
  return min(_edit_distance(exp1, exp2, k)[0], k)

def edit_substitutions(exp1, exp2):
  '''
  takes 2 expressions and returns the wild substitutions required to find the minimum distance
  '''
  exp1,exp2 = _prepare_exps(exp1, exp2)
  return _edit_distance(exp1, exp2, k)[1]
