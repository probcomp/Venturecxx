import Test.HUnit

import Language
import Venture

main = runTestTT $ test
  [ venture_main 1 [Predict $ Datum $ Number 1.0] >>= (@?= [Number 1.0])
  ]
