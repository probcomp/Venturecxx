import random

class SMap:
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

  def sample(self): return random.sample(self.a,1)[0]

  def asArray(self): return [t for (k,t) in self.a]
