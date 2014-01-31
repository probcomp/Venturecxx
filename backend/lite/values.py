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
  def getBool(self): return self.boolean

class VentureSymbol(value.VentureValue):
  def __init__(self,symbol): self.symbol = symbol
  def getSymbol(self): return self.symbol

class VentureArray(value.VentureValue):
  def __init__(self,array): self.array = array
  def getArray(self): return self.array

class VentureNil(value.VentureValue):
  def __init__(self): pass

class VenturePair(value.VentureValue):
  def __init__(self,first,rest):
    self.first = first
    self.rest = rest
  def getPair(self): return (self.first,self.rest)

class VentureSimplex(value.VentureValue):
  def __init__(self,simplex): self.simplex = simplex          
  def getSimplex(self): return self.simplex

class VentureDict(value.VentureValue):
  def __init__(self,d): self.dict = d
  def getDict(self): return self.dict

class VentureMatrix(value.VentureValue):
  def __init__(self,matrix): self.matrix = matrix
  def getMatrix(self): return self.matrix

## SPs and Environments as well
