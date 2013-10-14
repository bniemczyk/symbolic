#!/usr/bin/env python

'''
defines a number of "signature" heuristics for graphs
which can be used for trimming out candidate graphs
in isomorphism testing

some signatures are specific to specific types of graphs,
in that case, it is documented in the help for the particular
signature function
'''

import symath.util
from symath import symbols,wilds,WildResults
import numpy
import hashlib
import copy

GraphSummation = symbols('GraphSummation')
GraphDensity = symbols('GraphDensity')
GraphComplexity = symbols('GraphComplexity')
GraphPowerHash = symbols('GraphPowerHash')

def summation(graph):
  '''
  returns GraphSummation(nodes : int, edges : int)
  '''

  sum_out = 0
  sum_in = 0

  for n in graph.nodes.values():
    sum_out += len(n.outgoing)
    sum_in += len(n.incoming)

  assert sum_out == sum_in

  return GraphSummation(len(graph.nodes), sum_out)

def density(graph, loops=True):
  '''
  returns: GraphDensity(density : float)
  '''
  ns,es = wilds('ns es')
  vals = WildResults()

  if summation(graph).match(GraphSummation(ns,es), vals):
    pes = vals.ns.n * (vals.ns.n if loops else vals.ns.n - 1)
    return GraphDensity(vals.es.n / pes)
  else:
    raise BaseException("Unexpected result from summation()")

def complexity(graph):
  '''
  ONLY HAS MEANING FOR A CONTROL FLOW GRAPH

  calculates the cycolmatic complexity of a CFG

  returns: GraphComplexity(complexity : int)
  '''

  ns,es = wilds('ns es')
  vals = WildResults()

  if summation(graph).match(GraphSummation(ns, es), vals):
    return GraphComplexity((vals.es - vals.ns + len(graph.exit_nodes) * 2).simplify().n)
  else:
    raise BaseException("Unexpected result from summation()")

def powerhash(graph):
  '''
  TODO: MAY BE BROKEN SINCE SWITCHING TO SPARSE MATRIX FORMAT FOR GRAPHS

  based on: Approaches to Solving The Graph Isomorphism Problem by Jordy Eikenberry

  returns: Eikenberry(nodecount : int, hash : string)

  The algorithm:
    Take an adjacency matrix A of the graph

    remember that the (A ** n)[a,b] is the number of
    paths from a -> b of length n

    for every integer 1 .. n raise A to n and then 
    canonicalize the diagnol (via sorting) and use this
    as a token for the final hash

    isomorphic graphs will have the same count of 
    closed paths for every length

    a True result as usual only means it's a canidate, it does not imply isomorphism
  '''

  A = graph.adjacency_matrix()[1]
  Aprime = copy.copy(A)

  nc = len(A)
  d = symbols('d')

  hsum = []
  for n in range(len(A)):
    dia = list(numpy.diag(Aprime))
    dia.sort()
    Aprime = numpy.dot(Aprime,A)
    hsum.append(d(*dia))

  hsum = str(GraphPowerHash(*hsum))
  hsum = hashlib.sha256(hsum).hexdigest()

  return GraphPowerHash(nc, hsum)
