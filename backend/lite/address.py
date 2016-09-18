# Copyright (c) 2014 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

from collections import namedtuple

class EmptyList(object):
  def __iter__(self):
    return
    yield
  
  def __len__(self):
    return 0
  
  def __repr__(self):
    return str(list(self))
  
  def append(self, last):
    return List(last, self)

  def map(self, _f):
    return self
  
  def isEmpty(self):
    return True
  
  def __contains__(self, x):
    return False
  
  def remove(self, _x):
    return self
  
emptyList = EmptyList()

class List(object):
  """Functional list data structure.
  Note that order is reversed from the traditional
  scheme implementation. That is, insertion (via
  append) is done at the end of the list."""
  
  def __init__(self, last, rest=emptyList):
    self.last = last
    self.rest = rest
  
  # FIXME: quadratic runtime :(
  # even python3's "yield from" doesn't work
  def __iter__(self):
    for i in self.rest:
      yield i
    yield self.last
  
  def __len__(self):
    return 1 + len(self.rest)
  
  def __repr__(self):
    return str(list(self))
  
  def append(self, last):
    return List(last, self)

  def map(self, f):
    return self.rest.map(f).append(f(self.last))
  
  def isEmpty(self):
    return False
  
  def __contains__(self, x):
    if x == self.last:
      return True
    return x in self.rest
  
  def remove(self, x):
    if x == self.last:
      return self.rest
    return self.rest.remove(x).append(self.last)

class Address(List):
  """Maintains a call stack."""
  def __init__(self, index, stack=emptyList):
    super(Address, self).__init__(index, stack)
  
  def request(self, index):
    """Make a new stack frame."""
    return Address(index, self)
  
  def extend(self, index):
    """Extend the current stack frame."""
    return Address(self.last.append(index), self.rest)
  
  def asList(self):
    """Converts to nested lists."""
    return map(list, list(self))

  def asFrozenList(self):
    return tuple(map(tuple, list(self)))

  def __eq__(self, other):
    if not isinstance(other, Address):
      return False
    return self.asFrozenList() == other.asFrozenList()

  def __hash__(self):
    return hash(self.asFrozenList())

emptyAddress = Address(emptyList)

def directive_address(did):
  return Address(List(did))

def request(addr, index):
  return addr.request(index)

def extend(addr, index):
  return addr.extend(index)

# def top_frame(addr):
#   return addr.last

def append(loc, index):
  return loc.append(index)

class EmptyAddress(namedtuple('EmptyAddress', [])):
  def asList(self):
    return self.asAddress().asList()
  def asAddress(self):
    return Address(emptyList)
empty_address = EmptyAddress

class DirectiveAddress(namedtuple('DirectiveAddress', ["did"])):
  def asList(self):
    return self.asAddress().asList()
  def asAddress(self):
    return Address(List(self.did))
directive_address = DirectiveAddress

class RequestAddress(namedtuple('RequestAddress', ["app_addr", "req_id"])):
  def __init__(self, app_addr, req_id):
    assert _is_address(app_addr)
    super(RequestAddress, self).__init__(app_addr, req_id)
  def asList(self):
    return self.asAddress().asList()
  def asAddress(self):
    return self.app_addr.asAddress().request(self.req_id.asList())
request = RequestAddress

class SubexpressionAddress(namedtuple('SubexpressionAddress', ["sup_exp", "index"])):
  def __init__(self, sup_exp, index):
    assert _is_address(sup_exp)
    super(SubexpressionAddress, self).__init__(sup_exp, index)
  def asList(self):
    return self.asAddress().asList()
  def asAddress(self):
    return self.sup_exp.asAddress().extend(self.index)
extend = SubexpressionAddress

def _is_address(thing):
  return isinstance(thing, EmptyAddress) or \
    isinstance(thing, DirectiveAddress) or \
    isinstance(thing, RequestAddress) or \
    isinstance(thing, SubexpressionAddress)

class ReqLoc(namedtuple('ReqLoc', ["req_id"])):
  # Used by mem
  def asList(self):
    return List(self.req_id)
req_frame = ReqLoc

class DirectiveLoc(namedtuple('DirectiveLoc', ["did"])):
  def asList(self):
    return List(self.did)

class SubexpressionLoc(namedtuple('SubexpressionLoc', ["sup_exp", "index"])):
  def asList(self):
    return self.sup_exp.asList().append(self.index)
append = SubexpressionLoc

def top_frame(addr):
  if isinstance(addr, DirectiveAddress):
    return DirectiveLoc(addr.did)
  if isinstance(addr, SubexpressionAddress):
    return SubexpressionLoc(top_frame(addr.sup_exp), addr.index)
  if isinstance(addr, RequestAddress):
    # Relies on convention that compound procedures use their body
    # locations as request ids
    return addr.req_id

def jsonable_address(addr):
  assert _is_address(addr)
  if isinstance(addr, DirectiveAddress):
    return "/" + str(addr.did)
  if isinstance(addr, RequestAddress):
    # XXX This is not the same addressing convention as Mite.  There
    # the requests are identified by the maker node of the requesting
    # SP, not the application node that made the request.
    return jsonable_address(addr.app_addr) + "/request"
  if isinstance(addr, SubexpressionAddress):
    return jsonable_address(addr.sup_exp) + "/" + str(addr.index)
