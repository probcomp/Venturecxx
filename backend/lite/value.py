from abc import ABCMeta, abstractmethod

class VentureValue(object):
  __metaclass__ = ABCMeta

  def getNumber(self): raise Exception("Cannot convert %s to number" % type(self))
  def getBool(self): raise Exception("Cannot convert %s to bool" % type(self))
