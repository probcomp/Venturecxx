# Invariants that should hold about VentureValue objects

from venture.test.config import in_backend
from venture.test.randomized import checkTypedProperty
import venture.lite.value as vv

@in_backend("none")
def testEquality():
  checkTypedProperty(propEquality, vv.AnyType())

def propEquality(value):
  assert value.equal(value)

@in_backend("none")
def testLiteToStack():
  checkTypedProperty(propLiteToStack, vv.AnyType())

def propLiteToStack(val):
  assert val.equal(vv.VentureValue.fromStackDict(val.asStackDict()))

