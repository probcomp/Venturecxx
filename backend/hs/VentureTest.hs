import Test.HUnit

import Language
import Venture

main = runTestTT $ test
  [ venture_main 1 [Predict 1] >>= (@?= [1])
  , venture_main 1 [Predict $ App (Lam ["x"] (Var "x")) [1]] >>= (@?= [1])
  -- (let (id ...) (id 1))
  , venture_main 1 [Predict $ v_let1 "id" (Lam ["x"] (Var "x")) (App (Var "id") [1])] >>= (@?= [1])
  -- K combinator
  , venture_main 1 [Predict $ App (App k [1]) [2]] >>= (@?= [1])
  ]
    where k = (Lam ["x"] (Lam ["y"] (Var "x")))
