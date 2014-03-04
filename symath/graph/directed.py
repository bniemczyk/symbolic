#!/usr/bin/env python
from collections import deque
import copy
import scipy.sparse as sparse
import symath.datastructures

# it may be simpler to represent these as an adjacency matrix directly, but i plan
# on using some big ass graphs, so we save some memory by doing it this way
class DirectedGraph(object):
    class Node(object):
        def __init__(self, value):
            self.outgoing = set()
            self.incoming = set()
            self.value = value
            self.color = 'black'

    def clear():
        self.nodes = {}

    def get_color(self, node):
      return self.nodes[node].color

    def set_color(self, node, color):
      self.add_node(node)
      self.nodes[node].color = color

    def copy(self):
        return copy.deepcopy(self)

    def __init__(self, show_weights=False):
        self.nodes = {}
        self.edges = {}
        self.edge_weights = {}
        self.show_weights = show_weights

    @staticmethod
    def from_adjacency(nodes, adjM, **kargs):
      g = DirectedGraph(**kargs)

      nodesP = {}
      for k in nodes:
        nodesP[nodes[k]] = k
        g.add_node(k)

      # TODO: exploit adjacency of adjM if possible to make this faster
      #for i in range(len(adjM)):
      #  for j in range(len(adjM)):
      for (i,j) in zip(*adjM.nonzero()):
            #if adjM[i,j] > 0:
            g.connect(nodesP[i], nodesP[j])
            g.set_weight(adjM[i,j], nodesP[i], nodesP[j])

      return g

    def add_node(self, node):
        self.nodes.setdefault(node, DirectedGraph.Node(node))

    def connect(self, src, dst, edgeValue=None, weight=1):
        if src not in self.nodes:
            self.nodes[src] = DirectedGraph.Node(src)
        if dst not in self.nodes:
            self.nodes[dst] = DirectedGraph.Node(dst)

        self.nodes[src].outgoing.add(dst)
        self.nodes[dst].incoming.add(src)

        if edgeValue != None:
            self.edges.setdefault((src,dst), set()).add(edgeValue)

    def union(self, other):
      '''
      in place union
      '''

      for n in other.nodes:
        self.add_node(n)
        for m in other.nodes[n].outgoing:
          self.connect(n, m)
          if (n,m) in other.edges:
            for ev in other.edges[(n,m)]:
              self.connect(n, m, edgeValue=ev)

    def set_weight(self, w, src, dst, edgeValue=None):
      self.connect(src,dst,edgeValue)
      self.edge_weights[(src,dst,edgeValue)] = w

    def get_weight(self, src, dst, edgeValue=None):
      if not self.connectedQ(src,dst):
        return 0

      if (src,dst,edgeValue) not in self.edge_weights:
        return 1

      return self.edge_weights[(src,dst,edgeValue)]

    def disconnect(self, src, dst, edgeValue=None):

      if edgeValue != None:
        self.edges.setdefault((src,dst), set())
        if edgeValue in self.edges[(src,dst)]:
          self.edges[(src,dst)].remove(edgeValue)

      if (edgeValue == None or len(self.edges.setdefault((src,dst), set())) == 0) and dst in self.nodes[src].outgoing:
        self.nodes[src].outgoing.remove(dst)
        self.nodes[dst].incoming.remove(src)

    def strip_edges_to(self, dst):
        n = self.nodes[dst]
        for i in n.incoming:
            ni = self.nodes[i]
            ni.outgoing = filter(lambda x: x != dst, ni.outgoing)
        n.incoming = set()

    def strip_edges_from(self, src):
        n = self.nodes[src]
        for i in n.outgoing:
            ni = self.nodes[i]
            ni.incoming = filter(lambda x: x != src, ni.incoming)
        n.outgoing = set()

    def remove_node(self, n):
        self.strip_edges_to(n)
        self.strip_edges_from(n)
        del self.nodes[n]

    def __contains__(self, n):
        return n in self.nodes

    def connectedQ(self, src, dst):
        src = self.nodes[src]
        return dst in src.outgoing

    def walk(self, src, direction='outgoing', depthfirst=False):
        src = self.nodes.setdefault(src, DirectedGraph.Node(src))
        q = deque([(src,0)])
        seen = set([src.value])

        while len(q) > 0:
            node,level = q.popleft()
            yield (node.value,level)
            seen.add(node.value)

            linked = set()
            if direction in ['either', 'outgoing']:
                linked = linked.union(node.outgoing)
            if direction in ['either', 'incoming']:
                linked = linked.union(node.incoming)

            for i in linked:
                if i in seen:
                    continue
                else:
                    seen.add(i)
                    if depthfirst:
                      q.appendleft((self.nodes[i], level+1))
                    else:
                      q.append((self.nodes[i],level+1))

    def within_distance(self, src, distance, direction='outgoing'):
        for n,l in self.walk(src, direction=direction):
            if l > distance:
                break
            yield n

    def stackwalk(self, src, direction='outgoing'):
        src = self.nodes.setdefault(src, DirectedGraph.Node(src))
        q = deque([[src.value]])
        seen = set([src.value])

        while len(q) > 0:
            stack = q.popleft()
            yield stack
            seen.add(stack[-1])
            n = self.nodes[stack[-1]]
            for i in (n.outgoing if direction == 'outgoing' else n.incoming):
                if i in seen:
                    continue
                else:
                    newstack = copy.copy(stack)
                    newstack.append(i)
                    seen.add(i)
                    q.append(newstack)

    def adjacency_matrix(self):
        ids = {}
        nid = 0
        for i in self.nodes.values():
            ids[i.value] = nid
            nid += 1

        m = sparse.lil_matrix((nid,nid), dtype=float)
        for i in self.nodes.values():
            for j in i.outgoing:
                m[ids[i.value],ids[j]] = self.get_weight(i.value, j)

        return (ids, m)

    def _edge_count(self):
        ec = 0
        for n in self.nodes:
            ec += len(self.nodes[n].outgoing)
        return ec

    @property
    def exit_nodes(self):
      def _exit_nodes():
        for i in self.nodes.values():
          if len(i.outgoing) == 0:
            yield i

      return list(_exit_nodes())

    @property
    def start_node(self):
      for i in self.nodes.values():
        if len(i.incoming) == 0:
          return i

    def _write_dot_file(self,layout='dot'):
        import pydot
        import tempfile
        import os
        dotg = pydot.Dot('tmp', graph_type='digraph')

        dotnodes = {}
        for n in self.nodes:
            dotnodes[n] = pydot.Node(str(n), color=self.get_color(n))
            dotg.add_node(dotnodes[n])

        for n in self.nodes:
            for o in self.nodes[n].outgoing:
                if (n, o) in self.edges:
                    for e in self.edges[(n,o)]:
                        dotg.add_edge(pydot.Edge(dotnodes[n], dotnodes[o],label=e))
                else:
                  if self.show_weights:
                    dotg.add_edge(pydot.Edge(dotnodes[n], dotnodes[o], label=self.get_weight(n, o)))
                  else:
                    dotg.add_edge(pydot.Edge(dotnodes[n], dotnodes[o]))

        f = tempfile.NamedTemporaryFile(mode='w+b',delete=False)

        f.write(dotg.to_string())
        f.close()
        return f.name

    def visualize(self,layout='dot'):
      '''
      visualize using xdot
      '''
      import os

      fname = self._write_dot_file(layout=layout)
      try:
        os.system('xdot --filter=%s %s' % (layout, fname))
      finally:
        os.unlink(fname)

    def _repr_svg_(self):
      '''
      visualize in IPython
      '''
      from IPython.display import SVG
      import os
      import tempfile
      fname = self._write_dot_file()
      f = tempfile.NamedTemporaryFile(mode='w+b', delete=False)
      f.close()
      os.system('dot -Tsvg -o %s %s' % (f.name, fname))
      svg = SVG(filename=f.name)
      os.unlink(f.name)
      os.unlink(fname)
      return svg.data

if __name__ == '__main__':
    from algorithms import *

    dg = DirectedGraph()
    dg.connect('a', 'b')
    dg.connect('b', 'c')
    dg.connect('b', 'd')
    dg.connect('d', 'a')

    print graph_string(dg)

    for node,level in dg.walk('a'):
        print "%s level[%d]" % (node,level)

    for stack in dg.stackwalk('a'):
        print stack

    cylic = list(find_cylic_nodes(dg, 'a'))
    print 'cyclic nodes: %s' % (cylic)

    print 'domination set: %s' % (dominate_sets(dg, 'a'),)
    print 'domination tree: %s' % (graph_string(domtree(dominate_sets(dg, 'a'))))
    print 'loop headers: %s' % (loop_headers(dg, dominate_sets(dg, 'a'), 'a'))
