import Test.HUnit

import Language
import Venture

main = runTestTT $ test
  [ venture_main 1 [Predict $ Datum $ Number 1.0] >>= (@?= [Number 1.0])
  , venture_main 1 [Predict $ App (Lam ["x"] (Var "x")) [(Datum $ Number 1.0)]] >>= (@?= [Number 1.0])
  -- (let (id ...) (id 1))
  , venture_main 1 [Predict $ App (Lam ["id"] (App (Var "id") [(Datum $ Number 1.0)])) [(Lam ["x"] (Var "x"))]] >>= (@?= [Number 1.0])
  -- K combinator
  , venture_main 1 [Predict $ App (App (Lam ["x"] (Lam ["y"] (Var "x"))) [(Datum $ Number 1.0)]) [(Datum $ Number 2.0)]] >>= (@?= [Number 1.0])
  ]
