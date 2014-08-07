import random

class SMap(object):
  def __init__(self):
    self.d = {}
    self.a = []

  def __getitem__(self,k):
    return self.a[self.d[k]][1]


  def __setitem__(self,k,v):
    assert not k in self.d
    self.d[k] = len(self.a)
    self.a.append((k,v))

  def __delitem__(self,k):
    assert k in self.d
    index = self.d[k]
    lastIndex = len(self.a) - 1
    lastPair = self.a[lastIndex]

    self.d[lastPair[0]] = index
    self.a[index] = lastPair

    self.a.pop()
    del self.d[k]
    assert len(self.d) == len(self.a)

  def __contains__(self,k): return k in self.d
  def __len__(self): return len(self.a)

  def __str__(self): return "SMap: " + self._as_dict().__str__()
  def __repr__(self): return "SMap: " + self._as_dict().__repr__()

  def _as_dict(self):
    return {k:self[k] for k in self.d}

  def sample(self): return random.sample(self.a,1)[0]

  def keys(self): return self.d.keys()

  def values(self): return [v for (_,v) in self.a]
