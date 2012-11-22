def dict_reverse(d):
  rv = {}
  for k in d:
    rv[d[k]] = k
  return rv
