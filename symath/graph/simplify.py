#!/usr/bin/env python

import directed
import copy

def basic_blocks(graph):
  rv = graph.copy()

  cnt = True
  while cnt:
    cnt = False
    for k in rv.nodes.keys():
      n = rv.nodes[k]
      if len(n.outgoing) == 1:
        nxtk = n.outgoing.__iter__().next()
        nxt = rv.nodes[nxtk]
        if len(nxt.incoming) == 1:
          rv.disconnect(k, nxtk)
          for o in list(nxt.outgoing):
            cnt = True
            rv.disconnect(nxtk, o)
            rv.connect(k, o)

  for k in rv.nodes.keys():
    n = rv.nodes[k]
    if len(n.incoming) == 0 and len(n.outgoing) == 0:
      del rv.nodes[k]

  return rv

