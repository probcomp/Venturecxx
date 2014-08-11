import Control.Monad
import Control.Monad.Random.Class
import System.Exit
import Test.HUnit

import Language
import Venture
import Engine

import qualified Statistical as Stat

report :: (Show a) => Stat.Result a -> Assertion
report (Stat.Result (pval, msg)) = when (pval < 0.001) $ assertFailure $ show msg

basics :: Test
basics = test
  [ venture_main 1 [Predict 1] >>= (@?= [1])
  , venture_main 1 [Predict $ App v_id [1]] >>= (@?= [1])
  , venture_main 1 [Predict $ v_let1 "id" v_id (App (Var "id") [1])] >>= (@?= [1])
  -- K combinator
  , venture_main 1 [Predict $ App (App v_k [1]) [2]] >>= (@?= [1])
  ]
    where v_id = (Lam ["x"] (Var "x"))
          v_k = (Lam ["x"] (Lam ["y"] (Var "x")))

more :: (MonadRandom m) => [m Assertion]
more = map (liftM report)
  [ liftM (Stat.knownDiscrete [(Boolean True, 0.5), (Boolean False, 0.5)]) $ venture_main 100 flip_one_coin
  ]

main :: IO ()
main = do
  Counts { failures = f, errors = e } <- runTestTT $ test [basics, test (more :: [IO Assertion])]
  if f + e > 0 then
      exitWith $ ExitFailure $ f + e
  else
      exitSuccess
