import Control.Monad (when)
import System.Exit
import Test.HUnit

import Language
import Venture
import Engine

import qualified Statistical as Stat

report :: (Show a) => Stat.Result a -> Assertion
report (Stat.Result (pval, msg)) = when (pval < 0.001) $ assertFailure $ show msg

main = do
  Counts { failures = f, errors = e } <- runTestTT $ test
   ([ venture_main 1 [Predict 1] >>= (@?= [1])
    , venture_main 1 [Predict $ App v_id [1]] >>= (@?= [1])
    , venture_main 1 [Predict $ v_let1 "id" v_id (App (Var "id") [1])] >>= (@?= [1])
    -- K combinator
    , venture_main 1 [Predict $ App (App v_k [1]) [2]] >>= (@?= [1])
    ] ++ map report
    [ Stat.Result (1, "foo")
    ])
  if f + e > 0 then
      exitWith $ ExitFailure $ f + e
  else
      exitSuccess
    where v_id = (Lam ["x"] (Var "x"))
          v_k = (Lam ["x"] (Lam ["y"] (Var "x")))
