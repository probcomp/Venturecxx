import Test.HUnit

import Language
import Venture

main = runTestTT $ test
  [ venture_main 1 [Predict 1] >>= (@?= [1])
  , venture_main 1 [Predict $ App (Lam ["x"] (Var "x")) [1]] >>= (@?= [1])
  -- (let (id ...) (id 1))
  , venture_main 1 [Predict $ App (Lam ["id"] (App (Var "id") [1])) [(Lam ["x"] (Var "x"))]] >>= (@?= [1])
  -- K combinator
  , venture_main 1 [Predict $ App (App (Lam ["x"] (Lam ["y"] (Var "x"))) [1]) [2]] >>= (@?= [1])
  ]
