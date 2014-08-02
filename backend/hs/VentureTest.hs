import Test.HUnit

import Language
import Venture
import Engine

main = runTestTT $ test
  [ venture_main 1 [Predict 1] >>= (@?= [1])
  , venture_main 1 [Predict $ App v_id [1]] >>= (@?= [1])
  , venture_main 1 [Predict $ v_let1 "id" v_id (App (Var "id") [1])] >>= (@?= [1])
  -- K combinator
  , venture_main 1 [Predict $ App (App v_k [1]) [2]] >>= (@?= [1])
  ]
    where v_id = (Lam ["x"] (Var "x"))
          v_k = (Lam ["x"] (Lam ["y"] (Var "x")))
