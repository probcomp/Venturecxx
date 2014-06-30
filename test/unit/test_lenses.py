from venture.lite.value import VentureNumber
from venture.lite.mlens import real_lenses

def testLensSmoke1():
  v1 = VentureNumber(3)
  v2 = VentureNumber(4)
  lenses = real_lenses([v1, [v2]])
  assert [lens.get() for lens in lenses] == [3,4]
  lenses[1].set(2)
  assert [lens.get() for lens in lenses] == [3,2]
  assert v2.number == 2
