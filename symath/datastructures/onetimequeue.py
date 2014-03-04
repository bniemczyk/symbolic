from collections import deque

class onetimequeue(object):

  def __init__ (self):
    self._q = deque()
    self._seen = set()

  def push(self, obj):
    if obj in self._seen:
      return

    self._seen.add(obj)
    self._q.append(obj)

  def pop(self):
    return self._q.popleft()

  def __len__(self):
    return len(self._q)
