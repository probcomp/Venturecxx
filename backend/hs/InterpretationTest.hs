{-# LANGUAGE FlexibleContexts #-}

module InterpretationTest where

import Control.Monad
import Control.Monad.Random.Class
import Data.Maybe
import Data.Random.Distribution.Normal
import Test.HUnit

import Language hiding (Value)
import Examples
import Venture (Directive(..))
import InferenceInterpreter
import Trace (Valuable, fromValue, Value, var, lam, app)

import qualified Statistical as Stat

report :: (Show a) => Stat.Result a -> Assertion
report (Stat.Result (pval, msg)) = when (pval < 0.001) $ assertFailure $ show msg

basics :: Test
basics = test
  [ venture_main 1 [Predict 1] >>= (@?= [1])
  , venture_main 1 [Predict $ app v_id [1]] >>= (@?= [1])
  , venture_main 1 [Predict $ v_let1 "id" v_id (app (var "id") [1])] >>= (@?= [1])
  -- K combinator
  , venture_main 1 [Predict $ app (app v_k [1]) [2]] >>= (@?= [1])
  ]
    where v_id = (lam ["x"] (var "x"))
          v_k = (lam ["x"] (lam ["y"] (var "x")))

downsample :: Int -> [a] -> [a]
downsample _ [] = []
downsample n (x:xs) = x:(downsample n $ drop (n-1) xs)

samples :: (MonadRandom m, Valuable Double a) => [Directive Double] -> m [a]
samples prog = liftM (downsample 20) $ liftM (map $ fromJust . fromValue) $ venture_main 1000 prog

more :: (MonadRandom m) => [m Assertion]
more = map (liftM report)
  [ liftM (Stat.knownDiscrete [(Boolean True, 0.5), (Boolean False, 0.5)]) $ venture_main 100 flip_one_coin
  , liftM (Stat.knownDiscrete [(1, 0.5), (2, 0.5)]) $ venture_main 100 condition_on_flip
  , liftM (Stat.knownContinuous (Normal 0.0 2.0 :: Normal Double)) $ liftM (map $ fromJust . fromValue) $ venture_main 100 (single_normal :: [Directive Double])
  , liftM (Stat.knownContinuous (Normal 0.0 (sqrt 8.0) :: Normal Double)) $ samples chained_normals
  , liftM (Stat.knownContinuous (Normal 2.0 (sqrt 2.0) :: Normal Double)) $ samples observed_chained_normals
  , liftM (Stat.knownContinuous (Normal 2.0 (sqrt 2.0) :: Normal Double)) $ samples observed_chained_normals_lam
    -- list_of_coins does not appear to be a very interesting example
  , liftM (Stat.knownDiscrete [(True, 0.75), (False, 0.25)]) $ samples beta_binomial
  , liftM (Stat.knownDiscrete [(True, 0.75), (False, 0.25)]) $ samples cbeta_binomial
  , liftM (Stat.knownDiscrete [(Boolean True, 0.5), (Boolean False, 0.5)]) $ venture_main 100 self_select_1
  , liftM (Stat.knownDiscrete [(Boolean True, 0.5), (0, 0.5)]) $ venture_main 100 self_select_2
    -- TODO Test the two mem examples
  , liftM (Stat.knownDiscrete [(True, 0.5), (False, 0.5)]) $ liftM (map checkList) $ samples uncollapsed_conditional_and_coupled
  , liftM (Stat.knownDiscrete [(True, 0.5), (False, 0.5)]) $ liftM (map checkList) $ samples conditional_and_coupled
  , liftM (Stat.knownDiscrete [(True, 0.75), (False, 0.25)]) $ samples whether_a_node_is_random_can_change
  ]
    where checkList :: Value Double -> Bool
          checkList (List _) = True
          checkList (Boolean False) = False
          checkList _ = error "What?"

-- More testing possibilities
-- - Test mem more?
--   - Make sure that I do not leak anything (but especially not memoized
--     SRId entries) under inference with programs involving mem.
-- - Do more tests on the interaction between brush, collapsed state,
--   mem, and observations.  Is there anything here besides the
--   (observe (max (normal .) (normal .)) 0) can of bugs?

-- Known bugs:
-- - whether_a_node_is_random_can_change successfully confuses the
--   _randoms field of the Trace, but it is not clear how to get
--   measurably incorrect behavior from this
--   - Presumably the fix would be to insert an approprate
--     isRandomNode check into regenValue somewhere; is a symmetric
--     affordance needed for detach?
-- - self_select_2 (but not self_select_1) leaks (empty) SPRecords
--   (presumably for the lambdas that v_if desugars into)

tests :: Test
tests = test [basics, test (more :: [IO Assertion])]
