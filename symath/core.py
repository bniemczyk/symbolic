#!/usr/bin/env python
# this only exists because sympy crashes IDAPython
# for general use sympy is much more complete

import traceback
import types
import copy
import operator
from memoize import Memoize


def _order(a,b):
  '''
  used internally to put shit in canonical order
  '''
  if isinstance(a, Number):
    if(isinstance(b, Number)):
      return -1 if a.n < b.n else (0 if a.n == b.n else 1)
    return -1
  if isinstance(b, Number):
    return 1
  else:
    return -1 if str(a) < str(b) else (0 if str(a) == str(b) else 1)

class _Symbolic(tuple):

  def walk(self, *fns):
    rv = self
    for fn in fns:
      rv = fn(rv)
    #print "%s.walk() -> %s" % (self, rv)
    return rv

  def _dump(self):
    return {
        'name': self.name,
        'id': id(self)
        }

  def _canonicalize(self):
    '''
    overridden by some subtypes
     - should return a canonical version of itself
    '''
    return self

  def substitute(self, subs):
    '''
    takes a dictionary of substitutions
    returns itself with substitutions made
    '''
    if self in subs:
      self = subs[self]

    return self

  def __eq__(self, other):
    return type(self) == type(other) and self.name == other.name

  def __ne__(self, other):
    return not self.__eq__(other)

  def __hash__(self):
    return id(self)

  def __getitem__(self, num):
    if num == 0:
      return self

    raise BaseException("Invalid index")

  def __len__(self):
    return 1

  # arithmetic overrides
  def __mul__(self, other):
    return Fn.Mul(self, other)

  def __pow__(self, other):
    return Fn.Pow(self, other)

  def __rpow__(self, other):
    return Fn.Pow(other, self)

  def __div__(self, other):
    return Fn.Div(self, other)

  def __add__(self, other):
    return Fn.Add(self, other)

  def __sub__(self, other):
    return Fn.Sub(self, other)

  def __or__(self, other):
    return Fn.BitOr(self, other)

  def __and__(self, other):
    return Fn.BitAnd(self, other)

  def __xor__(self, other):
    return Fn.BitXor(self, other)

  def __rmul__(self, other):
    return Fn.Mul(other, self)

  def __rdiv__(self, other):
    return Fn.Div(other, self)

  def __radd__(self, other):
    return Fn.Add(other, self)

  def __rsub__(self, other):
    return Fn.Sub(other, self)

  def __ror__(self, other):
    return Fn.BitOr(other, self)

  def __rand__(self, other):
    return Fn.BitAnd(other, self)

  def __rxor__(self, other):
    return Fn.BitXor(other, self)

  def __rshift__(self, other):
    return Fn.RShift(self, other)

  def __lshift__(self, other):
    return Fn.LShift(self, other)

  def __rrshift__(self, other):
    return Fn.RShift(other, self)

  def __rlshift__(self, other):
    return Fn.LShift(other, self)

  def __neg__(self):
    return self * -1

class Boolean(int):

  def __new__(typ, b):
    self = int.__new__(typ, 1 if b else 0)
    self.name = str(b)
    self.boolean = b
    return self

  def __str__(self):
    return str(self.boolean)

  def __repr__(self):
    return str(self)

class Number(_Symbolic):

  IFORMAT = str
  FFORMAT = str

  def __new__(typ, n):
    n = float(n)
    self = _Symbolic.__new__(typ)
    self.name = str(n)
    self.n = n
    return self

  def __eq__(self, other):
    if isinstance(other, _Symbolic):
      return super(Number, self).__eq__(other)
    else:
      return self.n == other

  def __ne__(self, other):
    if isinstance(other, _Symbolic):
      return super(Number, self).__ne__(other)
    else:
      return self.n != other

  def __str__(self):
    if self.n.is_integer():
      return Number.IFORMAT(int(self.n))
    else:
      return Number.FFORMAT(self.n)

  def __repr__(self):
    return str(self)

  # arithmetic overrides
  def __neg__(self):
    return symbolic(self.n.__neg__())

  def __mul__(self, other):
    other = symbolic(other)

    if isinstance(other, Number):
      return symbolic(self.n.__mul__(other.n))

    return symbolic(other.__rmul__(self))

  def __pow__(self, other):
    other = symbolic(other)

    if isinstance(other, Number):
      return symbolic(self.n ** other.n)

    return symbolic(other.__rpow__(self))

  def __rpow__(self, other):
    other = symbolic(other)

    if isinstance(other, Number):
      return symbolic(other.n ** self.n)

    return symbolic(other.__pow__(self))

  def __div__(self, other):
    other = symbolic(other)

    if isinstance(other, Number):
      return symbolic(self.n.__div__(other.n))

    return symbolic(other.__rdiv__(self.n))

  def __add__(self, other):
    other = symbolic(other)

    if isinstance(other, Number):
      return symbolic(self.n.__add__(other.n))

    return symbolic(other.__radd__(self.n))

  def __sub__(self, other):
    other = symbolic(other)

    if isinstance(other, Number):
      return symbolic(self.n.__sub__(other.n))

    return symbolic(other.__rsub__(self.n))

  def __or__(self, other):
    other = symbolic(other)

    if isinstance(other, Number):
      return symbolic(int(self.n) | int(other.n))

    return other.__ror__(self)

  def __and__(self, other):
    other = symbolic(other)

    if isinstance(other, Number):
      return symbolic(int(self.n) & int(other.n))

    return symbolic(other).__rand__(int(self.n))

  def __xor__(self, other):
    other = symbolic(other)

    if isinstance(other, Number):
      return symbolic(int(self.n).__xor__(int(other.n)))

    return symbolic(other.__rxor__(int(self.n)))

  def __rshift__(self, other):
    other = symbolic(other)

    if isinstance(other, Number):
      return symbolic(int(self.n) >> int(other.n))

    return symbolic(other.__rrshift__(self))

  def __lshift__(self, other):
    other = symbolic(other)

    if isinstance(other, Number):
      return symbolic(int(self.n) << int(other.n))

    return symbolic(other.__rlshift__(self))

  def __rmul__(self, other):
    if not isinstance(other, Number):
      other = symbolic(other)

    if isinstance(other, Number):
      return symbolic(self.n.__rmul__(other.n))

    return symbolic(other.__mul__(self.n))

  def __rdiv__(self, other):
    if not isinstance(other, Number):
      other = symbolic(other)

    if isinstance(other, Number):
      return symbolic(self.n.__rdiv__(other.n))

    return symbolic(other.__div__(self.n))

  def __radd__(self, other):
    if not isinstance(other, Number):
      other = symbolic(other)

    if isinstance(other, Number):
      return symbolic(self.n.__radd__(other.n))

    return symbolic(other.__add__(self.n))

  def __rsub__(self, other):
    if not isinstance(other, Number):
      other = symbolic(other)

    if isinstance(other, Number):
      return symbolic(self.n.__rsub__(other.n))

    return symbolic(other.__sub__(self.n))

  def __ror__(self, other):
    if not isinstance(other, Number):
      other = symbolic(other)

    if isinstance(other, Number):
      return symbolic(int(self.n).__ror__(int(other.n)))

    return symbolic(int(other.n).__or__(int(self.n)))

  def __rand__(self, other):
    if not isinstance(other, Number):
      other = symbolic(other)

    if isinstance(other, Number):
      return symbolic(int(self.n).__rand__(int(other.n)))

    return symbolic(int(other.n).__and__(int(self.n)))

  def __rxor__(self, other):
    if not isinstance(other, Number):
      other = symbolic(other)

    if isinstance(other, Number):
      return symbolic(int(self.n) ^ int(other.n))

    return symbolic(int(other.n) ^ int(self.n))

  def __rrshift__(self, other):
    other = symbolic(other)

    if isinstance(other, Number):
      return symbolic(int(other.n) >> int(self.n))

    return symbolic(other.__rshift__(self))

  def __rlshift__(self, other):
    other = symbolic(other)

    if isinstance(other, Number):
      return symbolic(int(other.n) >> int(self.n))

    return symbolic(other.__lshift__(self))

class Wild(_Symbolic):
  '''
  wilds will not be equal even if they have the same name
  but the same *instance* will be equal to itself

  the main part of this is for substituting patterns -
   this is not implemented yet
  '''

  def __new__(typ, name, **kargs):
    self = _Symbolic.__new__(typ)
    self.name = name
    self.kargs = kargs
    self.iswild = True
    return self

  def __str__(self):
    return self.name

  def __repr__(self):
    return str(self)

  def __call__(self, *args):
    return Fn(self, *args)

  def _dump(self):
    return {
        'type': type(self),
        'name': self.name,
        'kargs': self.kargs,
        'iswild': self.iswild,
        'id': id(self)
        }

class Symbol(Wild):
  '''
  symbols with the same name will be equal
  (and in fact are wilds guaranteed to be the same instance)
  '''

  @Memoize
  def __new__(typ, name, **kargs):
    self = Wild.__new__(typ, name)
    self.name = name
    self.kargs = kargs
    self.iswild = False
    return self

class Fn(_Symbolic):

  def __new__(typ, fn, *args):
    '''
    arguments: Function, *arguments, **kargs
    valid keyword args:
      commutative (default False) - order of operands is unimportant
    '''

    if not isinstance(fn, _Symbolic):
      fn = symbolic(fn)
      return Fn.__new__(typ, fn, *args)

    for i in args:
      if not isinstance(i, _Symbolic):
        args = list(map(symbolic, args))
        return Fn.__new__(typ, fn, *args)

    self = _Symbolic.__new__(typ)
    kargs = fn.kargs
    self.kargs = fn.kargs

    if len(args) == 2 and 'numeric' in kargs:
      x = args[0]
      y = args[1]
      if isinstance(x, Number) and isinstance(y, Number):
        if 'cast' in kargs and kargs['cast'] != None:
          x = kargs['cast'](x.n)
          y = kargs['cast'](y.n)
        else:
          x = x.n
          y = y.n
        try:
          nfn = getattr(operator, kargs['numeric'])
          return symbolic(nfn(x,y))
        except:
          raise BaseException("Could not %s %s %s" % (x, kargs['numeric'], y))


    if 'zero' in kargs and kargs['zero'] in args:
      return kargs['zero']

    # if it's commutative, order the args in canonical order and call __new__ with that
    if 'commutative' in kargs and kargs['commutative']:
      args = list(args)
      oldargs = copy.copy(args)
      args.sort(cmp=_order)
      for i in range(len(args)):
        if oldargs[i] != args[i]:
          return Fn.__new__(typ, fn, *args)

    self.name = fn.name
    self.fn = fn
    self.args = args

    from simplify import simplify
    rv = simplify(self._canonicalize())._canonicalize()

    return rv

  def __eq__(self, other):
    if not type(self) == type(other):
      return False

    if len(self.args) != len(other.args):
      return False

    for i in range(len(self.args)):
      if self.args[i] != other.args[i]:
        return False

    return self.fn == other.fn

  def _dump(self):
    return {
        'id': id(self),
        'name': self.name,
        'fn': self.fn._dump(),
        'kargs': self.kargs,
        'args': list(map(lambda x: x._dump(), self.args)),
        'orig kargs': self.orig_kargs,
        'orig args': list(map(lambda x: x._dump(), self.orig_args))
        }

  def __call__(self, *args):
    return Fn(self, *args)

  def walk(self, *fns):
    args = list(map(lambda x: x.walk(*fns), self.args))
    newfn = self.fn.walk(*fns)
    rv = newfn(*args)
    for fn in fns:
      oldrv = rv
      rv = fn(rv)
      if oldrv != rv:
        #print "%s.walk(%s) -> %s" % (oldrv, fn, rv)
        pass
    return rv

  def substitute(self, subs):
    args = list(map(lambda x: x.substitute(subs), self.args))
    newfn = self.fn.substitute(subs)
    self = Fn(newfn, *args)

    if self in subs:
      self = subs[self]

    return self

  def __getitem__(self, n):
    if n == 0:
      return self.fn

    return self.args[n - 1]

  def __len__(self):
    return len(self.args) + 1

  def _get_assoc_arguments(self):
    rv = []

    args = list(self.args)
    def _(a, b):
      if (isinstance(a, Fn) and a.fn == self.fn) and not (isinstance(b, Fn) and b.fn == self.fn):
        return -1

      if (isinstance(b, Fn) and b.fn == self.fn) and not (isinstance(a, Fn) and a.fn == self.fn):
        return 1

      return _order(a, b)

    args.sort(_)

    for i in args:
      if isinstance(i, Fn) and i.fn == self.fn:
        for j in i._get_assoc_arguments():
          rv.append(j)
      else:
        rv.append(i)

    return rv

  def _canonicalize(self):
    # canonicalize the arguments first
    args = list(map(lambda x: x._canonicalize(), self.args))
    if tuple(args) != tuple(self.args):
      self = Fn(self.fn, *args)

    # if it's associative and one of the arguments is another instance of the
    # same function, canonicalize the order
    if len(self.args) == 2 and 'associative' in self.kargs and self.kargs['associative']:
      args = self._get_assoc_arguments()
      oldargs = tuple(args)
      args.sort(_order)
      if tuple(args) != oldargs:
        kargs = copy.copy(self.kargs)
        self = reduce(lambda a, b: Fn(self.fn, a, b), args)

    return self

  @staticmethod
  def LessThan(lhs, rhs):
    return Fn(stdops.LessThan, lhs, rhs)

  @staticmethod
  def GreaterThan(lhs, rhs):
    return Fn(stdops.GreaterThan, lhs, rhs)

  @staticmethod
  def LessThanEq(lhs, rhs):
    return Fn(stdops.LessThanEq, lhs, rhs)

  @staticmethod
  def GreaterThanEq(lhs, rhs):
    return Fn(stdops.GreaterThanEq, lhs, rhs)

  @staticmethod
  def Add(lhs, rhs):
    return Fn(stdops.Add, lhs, rhs)

  @staticmethod
  def Sub(lhs, rhs):
    return Fn(stdops.Sub, lhs, rhs)

  @staticmethod
  def Div(lhs, rhs):
    return Fn(stdops.Div, lhs, rhs)

  @staticmethod
  def Mul(lhs, rhs):
    return Fn(stdops.Mul, lhs, rhs)

  @staticmethod
  def Pow(lhs, rhs):
    return Fn(stdops.Pow, lhs, rhs)

  @staticmethod
  def RShift(lhs, rhs):
    return Fn(stdops.RShift, lhs, rhs)

  @staticmethod
  def LShift(lhs, rhs):
    return Fn(stdops.LShift, lhs, rhs)

  @staticmethod
  def BitAnd(lhs, rhs):
    return Fn(stdops.BitAnd, lhs, rhs)

  @staticmethod
  def BitOr(lhs, rhs):
    return Fn(stdops.BitOr, lhs, rhs)

  @staticmethod
  def BitXor(lhs, rhs):
    return Fn(stdops.BitXor, lhs, rhs)

  def __str__(self):
    if isinstance(self.fn, Symbol) and not self.name[0].isalnum() and len(self.args) == 2:
      return '(%s %s %s)' % (self.args[0], self.name, self.args[1])

    return '%s(%s)' % (self.fn, ','.join(map(str, self.args)))

  def __repr__(self):
    return str(self)

def symbols(symstr, **kargs):
  '''
  takes a string of symbols seperated by whitespace
  returns a tuple of symbols
  '''
  syms = symstr.split(' ')
  if len(syms) == 1:
    return Symbol(syms[0], **kargs)

  rv = []
  for i in syms:
    rv.append(Symbol(i, **kargs))

  return tuple(rv)

def wilds(symstr):
  '''
  takes a string of variable names seperated by whitespace
  returns a tuple of wilds
  '''
  syms = symstr.split(' ')
  if len(syms) == 1:
    return Wild(syms[0])

  rv = []
  for i in syms:
    rv.append(Wild(i))

  return tuple(rv)

def symbolic(obj, **kargs): 
  '''
  makes the symbolic version of an object
  '''
  if type(obj) in [type(0), type(0.0), type(0L)]:
    return Number(obj, **kargs)
  elif type(obj) == type('str'):
    return Symbol(obj, **kargs)
  elif type(obj) == type(True):
    return Boolean(obj, **kargs)
  elif isinstance(obj, _Symbolic):
    return obj
  else:
    msg = "Unknown type (%s) %s passed to symbolic" % (type(obj), obj)
    raise BaseException(msg)

import stdops
