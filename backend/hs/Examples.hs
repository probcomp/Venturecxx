{-# LANGUAGE ConstraintKinds #-}

module Examples where

import Control.Monad.Reader
import Control.Monad.Trans.State.Lazy
import Control.Monad.Random hiding (randoms) -- From cabal install MonadRandom
import Control.Lens  -- from cabal install lens

import Language hiding (Exp, Value, Env)
import Trace
import Utils
import Venture hiding (empty)
import Inference
import InferenceInterpreter

watching_infer' :: (MonadRandom m, Numerical num) =>
                   Address -> Int -> StateT (Trace m num) m [Value num]
watching_infer' address ct = replicateM ct (do
  Inference.resimulation_mh default_one
  gets $ fromJust "Value was not restored by inference" . valueOf
         . fromJust "Address became invalid after inference" . (lookupNode address))

watching_infer :: (MonadRandom m, Numerical num) =>
                  Address -> Int -> StateT (Model m num) m [Value num]
watching_infer address ct = trace `zoom` (watching_infer' address ct)

-- Expects the directives to contain exactly one Predict
simulation :: (MonadRandom m, Numerical num) =>
              Int -> [Directive num] -> StateT (Model m num) m [Value num]
simulation ct ds = do
  target <- liftM head (execute ds)
  watching_infer target ct

venture_main :: (MonadRandom m, Real num, Show num, Floating num, Enum num) =>
                Int -> [Directive num] -> m [Value num]
venture_main ct ds = do
  vs <- evalStateT (simulation ct ds) initial
  return $ vs

v_if :: Exp num -> Exp num -> Exp num -> Exp num
v_if p c a = app (app (var "select") [p, (lam [] c), (lam [] a)]) []

v_let1 :: String -> Exp num -> Exp num -> Exp num
v_let1 name val body = app (lam [name] body) [val]

flip_one_coin :: [Directive num]
flip_one_coin = [Predict $ app (var "bernoulli") []]
-- venture_main 10 flip_one_coin
-- liftM discreteHistogram $ venture_main 100 flip_one_coin

single_normal :: (Num num) => [Directive num]
single_normal = [Predict $ app (var "normal") [0, 2]]
-- venture_main 10 single_normal
-- (liftM (histogram 10) $ liftM (map $ fromJust "foo" . fromValue) $ venture_main 500 $ single_normal) >>= printHistogram

condition_on_flip :: (Num num) => [Directive num]
condition_on_flip = [Predict $ v_if (app (var "bernoulli") []) 1 2]
-- venture_main 10 $ condition_on_flip
-- liftM discreteHistogram $ venture_main 100 condition_on_flip

chained_normals :: (Num num) => [Directive num]
chained_normals =
    [ Assume "x" $ app (var "normal") [0, 2]
    , Assume "y" $ app (var "normal") [(var "x"), 2]
    , Predict $ var "y"
    ]
-- venture_main 10 $ chained_normals
-- (liftM (histogram 10) $ liftM (map $ fromJust "foo" . fromValue) $ venture_main 500 $ chained_normals) >>= printHistogram

observed_chained_normals :: (Num num) => [Directive num]
observed_chained_normals =
    [ Assume "x" $ app (var "normal") [0, 2]
    , Assume "y" $ app (var "normal") [(var "x"), 2]
    , Observe (var "y") 4
    , Predict $ var "x"
    ]
-- venture_main 10 $ observed_chained_normals
-- (liftM (histogram 10) $ liftM (map $ fromJust "foo" . fromValue) $ venture_main 500 $ observed_chained_normals) >>= printHistogram

-- This example forces propagation of constraints backwards through
-- forwarding outputs.  Predicting "y" should yield 4, and predicting
-- "x" should look like observed_chained_normals.
observed_chained_normals_lam :: (Num num) => [Directive num]
observed_chained_normals_lam =
    [ Assume "x" $ app (var "normal") [0, 2]
    , Assume "y" $ app (var "normal") [(var "x"), 2]
    , Assume "z" $ app (lam ["q"] (var "q")) [(var "y")]
    , Observe (var "z") 4
    , Predict $ var "x"
    ]
-- venture_main 10 $ observed_chained_normals_lam
-- (liftM (histogram 10) $ liftM (map $ fromJust "foo" . fromValue) $ venture_main 500 $ observed_chained_normals_lam) >>= printHistogram

list_of_coins :: [Directive num]
list_of_coins = [Predict $ app (var "list") [flip, flip, flip]] where
    flip = app (var "bernoulli") []
-- join $ liftM sequence_ $ liftM (map $ putStrLn . show) $ venture_main 10 list_of_coins

-- Weighted coins
-- liftM discreteHistogram $ venture_main 100 [Predict $ app (var "weighted") [0.8]]

-- Beta Bernoulli (uncollapsed).  In Lisp syntax:
--  (assume make_coin (lambda (weight) (lambda () (weighted weight))))
--  (assume coin (make_coin (beta 1 1)))
--  (observe (coin) true)
--  (observe (coin) true)
--  (observe (coin) true)
--  (predict (coin))
beta_binomial :: (Num num) => [Directive num]
beta_binomial =
    [ Assume "make-coin" $ lam ["weight"] $ lam [] $ app (var "weighted") [var "weight"]
    , Assume "coin" $ app (var "make-coin") [app (var "beta") [1, 1]]
    , Observe (app (var "coin") []) (Boolean True)
    , Observe (app (var "coin") []) (Boolean True)
    , Observe (app (var "coin") []) (Boolean True)
    , Predict (app (var "coin") [])
    ]
-- liftM discreteHistogram $ venture_main 100 beta_binomial

-- Beta Bernoulli (collapsed).  In Lisp syntax:
--  (assume coin (make-cbeta-bernoulli 1 1))
--  (observe (coin) true)
--  (observe (coin) true)
--  (observe (coin) true)
--  (predict (coin))
cbeta_binomial :: (Num num) => [Directive num]
cbeta_binomial =
    [ Assume "coin" $ app (var "make-cbeta-bernoulli") [1, 1]
    , Observe (app (var "coin") []) (Boolean True)
    , Observe (app (var "coin") []) (Boolean True)
    , Observe (app (var "coin") []) (Boolean True)
    , Predict (app (var "coin") [])
    ]

-- liftM discreteHistogram $ venture_main 100 cbeta_binomial

-- (assume x (flip))
-- (predict (if x x false))
self_select_1 :: [Directive num]
self_select_1 =
    [ Assume "x" $ app (var "bernoulli") []
    , Predict $ v_if (var "x") (var "x") false
    ]
-- liftM discreteHistogram $ venture_main 100 self_select_1

-- (assume x (flip))
-- (predict (if x (if x x 1.0) 0.0))
self_select_2 :: (Num num) => [Directive num]
self_select_2 =
    [ Assume "x" $ app (var "bernoulli") []
    , Predict $ v_if (var "x") (v_if (var "x") (var "x") 1) 0
    ]
-- liftM discreteHistogram $ venture_main 100 self_select_2

mem_1 :: (Num num) => [Directive num]
mem_1 =
    [ Assume "coins" $ app (var "mem") [lam ["i"] (app (var "bernoulli") [])]
    , Predict $ app (var "list") [flip 1, flip 1, flip 1, flip 2, flip 2, flip 2, flip 3, flip 3, flip 3]
    ] where
    flip k = app (var "coins") [k]
-- join $ liftM sequence_ $ liftM (map $ putStrLn . show) $ venture_main 10 mem_1
-- Each triple should have the same value in each output, but vary across outputs

mem_2 :: (Num num) => [Directive num]
mem_2 =
    [ Assume "coins_p" $ app (var "mem") [lam ["i"] (app (var "bernoulli") [])]
    , Assume "coins" $ v_if (app (var "bernoulli") []) (var "coins_p") (var "coins_p")
    , Predict $ app (var "list") [flip 1, flip 1, flip 1, flip 2, flip 2, flip 2, flip 3, flip 3, flip 3]
    ] where
    flip k = app (var "coins") [k]
-- join $ liftM sequence_ $ liftM (map $ putStrLn . show) $ venture_main 10 mem_2

uncollapsed_conditional_and_coupled :: (Num num) => [Directive num]
uncollapsed_conditional_and_coupled =
    [ Assume "weight" $ app (var "beta") [1,1]
    , Assume "coin" $ lam [] (app (var "weighted") [var "weight"])
    , Predict $ v_if coin
              (app (var "list") [coin, coin, coin])
              false
    ] where coin = (app (var "coin") [])
-- This should see "false" (rather than a list) about 50% of the time
-- join $ liftM sequence_ $ liftM (map $ putStrLn . show) $ liftM M.toList $ liftM discreteHistogram $ venture_main 500 uncollapsed_conditional_and_coupled

conditional_and_coupled :: (Num num) => [Directive num]
conditional_and_coupled =
    [ Assume "coin" $ app (var "make-cbeta-bernoulli") [1, 1]
    , Predict $ v_if coin
              (app (var "list") [coin, coin, coin])
              false
    ] where coin = (app (var "coin") [])
-- This should be equivalent to the uncollapsed one
-- join $ liftM sequence_ $ liftM (map $ putStrLn . show) $ liftM M.toList $ liftM discreteHistogram $ venture_main 500 conditional_and_coupled

whether_a_node_is_random_can_change :: [Directive num]
whether_a_node_is_random_can_change =
    [ Assume "coin" $ v_if (app (var "bernoulli") [])
             (lam [] true)
             (var "bernoulli")
    , Predict $ app (var "coin") []
    ]
-- venture_main 10 whether_a_node_is_random_can_change
-- liftM discreteHistogram $ venture_main 100 whether_a_node_is_random_can_change
