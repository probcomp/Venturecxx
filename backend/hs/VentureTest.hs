import Control.Monad
import Control.Monad.Random.Class
import Data.Maybe
import Data.Random.Distribution.Normal
import System.Exit
import Test.HUnit

import Language hiding (Value)
import Venture
import Engine
import Trace (Valuable, fromValue, Value)

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

downsample :: Int -> [a] -> [a]
downsample _ [] = []
downsample n (x:xs) = x:(downsample n $ drop (n-1) xs)

samples :: (MonadRandom m, Valuable a) => [Directive] -> m [a]
samples prog = liftM (downsample 20) $ liftM (map $ fromJust . fromValue) $ venture_main 1000 prog

more :: (MonadRandom m) => [m Assertion]
more = map (liftM report)
  [ liftM (Stat.knownDiscrete [(Boolean True, 0.5), (Boolean False, 0.5)]) $ venture_main 100 flip_one_coin
  , liftM (Stat.knownDiscrete [(1, 0.5), (2, 0.5)]) $ venture_main 100 condition_on_flip
  , liftM (Stat.knownContinuous (Normal 0.0 2.0 :: Normal Double)) $ liftM (map $ fromJust . fromValue) $ venture_main 100 single_normal
  , liftM (Stat.knownContinuous (Normal 0.0 (sqrt 8.0) :: Normal Double)) $ samples chained_normals
  , liftM (Stat.knownContinuous (Normal 2.0 (sqrt 2.0) :: Normal Double)) $ samples observed_chained_normals
  , liftM (Stat.knownContinuous (Normal 2.0 (sqrt 2.0) :: Normal Double)) $ samples observed_chained_normals_lam
    -- list_of_coins does not appear to be a very interesting example
  , liftM (Stat.knownDiscrete [(True, 0.75), (False, 0.25)]) $ samples beta_binomial
  , liftM (Stat.knownDiscrete [(True, 0.75), (False, 0.25)]) $ samples cbeta_binomial
  , liftM (Stat.knownDiscrete [(Boolean True, 0.5), (Boolean False, 0.5)]) $ venture_main 100 self_select_1
  , liftM (Stat.knownDiscrete [(1, 0.5), (0, 0.5)]) $ venture_main 100 self_select_2
    -- TODO Test the two mem examples
  , liftM (Stat.knownDiscrete [(True, 0.5), (False, 0.5)]) $ liftM (map checkList) $ samples uncollapsed_conditional_and_coupled
  , liftM (Stat.knownDiscrete [(True, 0.5), (False, 0.5)]) $ liftM (map checkList) $ samples conditional_and_coupled
  , liftM (Stat.knownDiscrete [(True, 0.75), (False, 0.25)]) $ samples whether_a_node_is_random_can_change
  ]
    where checkList :: Value -> Bool
          checkList (List _) = True
          checkList (Boolean False) = False
          checkList _ = error "What?"

main :: IO ()
main = do
  Counts { failures = f, errors = e } <- runTestTT $ test [basics, test (more :: [IO Assertion])]
  if f + e > 0 then
      exitWith $ ExitFailure $ f + e
  else
      exitSuccess
