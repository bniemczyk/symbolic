#!/usr/bin/env python

import core

def extract(a,b,rv=None):
  '''
  extract values from an expression
  returns a dictionary of wild names => values where b contains the wilds
  '''
  if rv == None:
    rv = {}

  if len(a) != len(b):
    return None

  if isinstance(b, core.Wild):
    if b.name in rv and rv[b.name] != a:
      return None
    rv[b.name] = a
    return rv
  elif len(b) > 1:
    for i in range(len(b)):
      if extract(a[i], b[i], rv) == None:
        return None
    return rv
  elif a == b:
    return rv
  else:
    return None

def match(a, b, valuestore=None):
  '''
  match is like == except it enforces that if the same wild is used in multiple places
  then the same value must be in each of those places
  '''

  if valuestore != None:
    valuestore.clear()

  d = extract(a,b)
  if d == None:
    return False

  for k in d:
    valuestore[k] = d[k]

  return True
