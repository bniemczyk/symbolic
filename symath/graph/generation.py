#!/usr/bin/env python
import directed
import random

def random_graph(nodecount, edgeprobability, directedEdges=True):

  '''
  Generate a random graph

  currently directedEdges must be True
  '''

  assert directedEdges == True
  rv = directed.DirectedGraph()

  for i in range(nodecount):
    rv.add_node(i)
    for j in range(nodecount):
      if random.random() <= edgeprobability:
        rv.connect(i, j)

  return rv
