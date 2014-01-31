from abc import ABCMeta, abstractmethod

class VentureValue(object):
  __metaclass__ = ABCMeta

  def getNumber(self): raise Exception("Cannot convert %s to number" % type(self))
  def getAtom(self): raise Exception("Cannot convert %s to atom" % type(self))
  def getBool(self): raise Exception("Cannot convert %s to bool" % type(self))
  def getSymbol(self): raise Exception("Cannot convert %s to symbol" % type(self))
  def getArray(self): raise Exception("Cannot convert %s to array" % type(self))
  def getPair(self): raise Exception("Cannot convert %s to pair" % type(self))
  def getSimplex(self): raise Exception("Cannot convert %s to simplex" % type(self))
  def getDict(self): raise Exception("Cannot convert %s to dict" % type(self))
  def getMatrix(self): raise Exception("Cannot convert %s to matrix" % type(self))
  def getSP(self): raise Exception("Cannot convert %s to sp" % type(self))
  def getEnvironment(self): raise Exception("Cannot convert %s to environment" % type(self))
