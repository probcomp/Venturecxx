import value

class VentureNumber(value.VentureValue):
  def __init__(self,number): self.number = number
  def getNumber(self): return self.number

class VentureAtom(value.VentureValue):
  def __init__(self,atom): self.atom = atom
  def getNumber(self): return self.atom
  def getBool(self): return self.atom

class VentureBool(value.VentureValue):
  def __init__(self,boolean): self.boolean = boolean

class VentureSymbol(value.VentureValue):
  def __init__(self,symbol): self.symbol = symbol

class VentureArray(value.VentureValue):
  def __init__(self,array): self.array = array
    
class VentureNil(value.VentureValue):
  def __init__(self): pass

class VenturePair(value.VentureValue):
  def __init__(self,first,rest):
    self.first = first
    self.rest = rest

class VentureSimplex(value.VentureValue):
  def __init__(self,simplex): self.simplex = simplex          

class VentureDict(value.VentureValue):
  def __init__(self,d): self.dict = d

class VentureMatrix(value.VentureValue):
  def __init__(self,matrix): self.matrix = matrix

## SPs and Environments as well
