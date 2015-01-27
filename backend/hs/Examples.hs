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

watching_infer' :: (MonadRandom m) => Address -> Int -> StateT (Trace m) m [Value]
watching_infer' address ct = replicateM ct (do
  Inference.resimulation_mh default_one
  gets $ fromJust "Value was not restored by inference" . valueOf
         . fromJust "Address became invalid after inference" . (lookupNode address))

watching_infer :: (MonadRandom m) => Address -> Int -> StateT (Model m) m [Value]
watching_infer address ct = trace `zoom` (watching_infer' address ct)

-- Expects the directives to contain exactly one Predict
simulation :: (MonadRandom m) => Int -> [Directive] -> StateT (Model m) m [Value]
simulation ct ds = do
  target <- liftM head (execute ds)
  watching_infer target ct

venture_main :: (MonadRandom m) => Int -> [Directive] -> m [Value]
venture_main ct ds = do
  vs <- evalStateT (simulation ct ds) initial
  return $ vs

v_if :: Exp -> Exp -> Exp -> Exp
v_if p c a = App (App (Var "select") [p, (Lam [] c), (Lam [] a)]) []

v_let1 :: String -> Exp -> Exp -> Exp
v_let1 name val body = App (Lam [name] body) [val]

flip_one_coin :: [Directive]
flip_one_coin = [Predict $ App (Var "bernoulli") []]
-- venture_main 10 flip_one_coin
-- liftM discreteHistogram $ venture_main 100 flip_one_coin

single_normal :: [Directive]
single_normal = [Predict $ App (Var "normal") [0, 2]]
-- venture_main 10 single_normal
-- (liftM (histogram 10) $ liftM (map $ fromJust "foo" . fromValue) $ venture_main 500 $ single_normal) >>= printHistogram

condition_on_flip :: [Directive]
condition_on_flip = [Predict $ v_if (App (Var "bernoulli") []) 1 2]
-- venture_main 10 $ condition_on_flip
-- liftM discreteHistogram $ venture_main 100 condition_on_flip

chained_normals :: [Directive]
chained_normals =
    [ Assume "x" $ App (Var "normal") [0, 2]
    , Assume "y" $ App (Var "normal") [(Var "x"), 2]
    , Predict $ Var "y"
    ]
-- venture_main 10 $ chained_normals
-- (liftM (histogram 10) $ liftM (map $ fromJust "foo" . fromValue) $ venture_main 500 $ chained_normals) >>= printHistogram

observed_chained_normals :: [Directive]
observed_chained_normals =
    [ Assume "x" $ App (Var "normal") [0, 2]
    , Assume "y" $ App (Var "normal") [(Var "x"), 2]
    , Observe (Var "y") 4
    , Predict $ Var "x"
    ]
-- venture_main 10 $ observed_chained_normals
-- (liftM (histogram 10) $ liftM (map $ fromJust "foo" . fromValue) $ venture_main 500 $ observed_chained_normals) >>= printHistogram

-- This example forces propagation of constraints backwards through
-- forwarding outputs.  Predicting "y" should yield 4, and predicting
-- "x" should look like observed_chained_normals.
observed_chained_normals_lam :: [Directive]
observed_chained_normals_lam =
    [ Assume "x" $ App (Var "normal") [0, 2]
    , Assume "y" $ App (Var "normal") [(Var "x"), 2]
    , Assume "z" $ App (Lam ["q"] (Var "q")) [(Var "y")]
    , Observe (Var "z") 4
    , Predict $ Var "x"
    ]
-- venture_main 10 $ observed_chained_normals_lam
-- (liftM (histogram 10) $ liftM (map $ fromJust "foo" . fromValue) $ venture_main 500 $ observed_chained_normals_lam) >>= printHistogram

list_of_coins :: [Directive]
list_of_coins = [Predict $ App (Var "list") [flip, flip, flip]] where
    flip = App (Var "bernoulli") []
-- join $ liftM sequence_ $ liftM (map $ putStrLn . show) $ venture_main 10 list_of_coins

-- Weighted coins
-- liftM discreteHistogram $ venture_main 100 [Predict $ App (Var "weighted") [Datum $ Number 0.8]]

-- Beta Bernoulli (uncollapsed).  In Lisp syntax:
--  (assume make_coin (lambda (weight) (lambda () (weighted weight))))
--  (assume coin (make_coin (beta 1 1)))
--  (observe (coin) true)
--  (observe (coin) true)
--  (observe (coin) true)
--  (predict (coin))
beta_binomial :: [Directive]
beta_binomial =
    [ Assume "make-coin" $ Lam ["weight"] $ Lam [] $ App (Var "weighted") [Var "weight"]
    , Assume "coin" $ App (Var "make-coin") [App (Var "beta") [1, 1]]
    , Observe (App (Var "coin") []) (Boolean True)
    , Observe (App (Var "coin") []) (Boolean True)
    , Observe (App (Var "coin") []) (Boolean True)
    , Predict (App (Var "coin") [])
    ]
-- liftM discreteHistogram $ venture_main 100 beta_binomial

-- Beta Bernoulli (collapsed).  In Lisp syntax:
--  (assume coin (make-cbeta-bernoulli 1 1))
--  (observe (coin) true)
--  (observe (coin) true)
--  (observe (coin) true)
--  (predict (coin))
cbeta_binomial :: [Directive]
cbeta_binomial =
    [ Assume "coin" $ App (Var "make-cbeta-bernoulli") [1, 1]
    , Observe (App (Var "coin") []) (Boolean True)
    , Observe (App (Var "coin") []) (Boolean True)
    , Observe (App (Var "coin") []) (Boolean True)
    , Predict (App (Var "coin") [])
    ]

-- liftM discreteHistogram $ venture_main 100 cbeta_binomial

-- (assume x (flip))
-- (predict (if x x false))
self_select_1 :: [Directive]
self_select_1 =
    [ Assume "x" $ App (Var "bernoulli") []
    , Predict $ v_if (Var "x") (Var "x") (Datum $ Boolean False)
    ]
-- liftM discreteHistogram $ venture_main 100 self_select_1

-- (assume x (flip))
-- (predict (if x (if x x 1.0) 0.0))
self_select_2 :: [Directive]
self_select_2 =
    [ Assume "x" $ App (Var "bernoulli") []
    , Predict $ v_if (Var "x") (v_if (Var "x") (Var "x") 1) 0
    ]
-- liftM discreteHistogram $ venture_main 100 self_select_2

mem_1 :: [Directive]
mem_1 =
    [ Assume "coins" $ App (Var "mem") [Lam ["i"] (App (Var "bernoulli") [])]
    , Predict $ App (Var "list") [flip 1, flip 1, flip 1, flip 2, flip 2, flip 2, flip 3, flip 3, flip 3]
    ] where
    flip k = App (Var "coins") [k]
-- join $ liftM sequence_ $ liftM (map $ putStrLn . show) $ venture_main 10 mem_1
-- Each triple should have the same value in each output, but vary across outputs

mem_2 :: [Directive]
mem_2 =
    [ Assume "coins_p" $ App (Var "mem") [Lam ["i"] (App (Var "bernoulli") [])]
    , Assume "coins" $ v_if (App (Var "bernoulli") []) (Var "coins_p") (Var "coins_p")
    , Predict $ App (Var "list") [flip 1, flip 1, flip 1, flip 2, flip 2, flip 2, flip 3, flip 3, flip 3]
    ] where
    flip k = App (Var "coins") [k]
-- join $ liftM sequence_ $ liftM (map $ putStrLn . show) $ venture_main 10 mem_2

uncollapsed_conditional_and_coupled :: [Directive]
uncollapsed_conditional_and_coupled =
    [ Assume "weight" $ App (Var "beta") [1,1]
    , Assume "coin" $ Lam [] (App (Var "weighted") [Var "weight"])
    , Predict $ v_if coin
              (App (Var "list") [coin, coin, coin])
              (Datum $ Boolean False)
    ] where coin = (App (Var "coin") [])
-- This should see "false" (rather than a list) about 50% of the time
-- join $ liftM sequence_ $ liftM (map $ putStrLn . show) $ liftM M.toList $ liftM discreteHistogram $ venture_main 500 uncollapsed_conditional_and_coupled

conditional_and_coupled :: [Directive]
conditional_and_coupled =
    [ Assume "coin" $ App (Var "make-cbeta-bernoulli") [1, 1]
    , Predict $ v_if coin
              (App (Var "list") [coin, coin, coin])
              (Datum $ Boolean False)
    ] where coin = (App (Var "coin") [])
-- This should be equivalent to the uncollapsed one
-- join $ liftM sequence_ $ liftM (map $ putStrLn . show) $ liftM M.toList $ liftM discreteHistogram $ venture_main 500 conditional_and_coupled

whether_a_node_is_random_can_change :: [Directive]
whether_a_node_is_random_can_change =
    [ Assume "coin" $ v_if (App (Var "bernoulli") [])
             (Lam [] $ Datum $ Boolean True)
             (Var "bernoulli")
    , Predict $ App (Var "coin") []
    ]
-- venture_main 10 whether_a_node_is_random_can_change
-- liftM discreteHistogram $ venture_main 100 whether_a_node_is_random_can_change
