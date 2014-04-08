module Venture where

import Debug.Trace
import Control.Monad.Reader
import Control.Monad.Trans.State.Lazy
import Control.Monad.Random hiding (randoms) -- From cabal install MonadRandom

import Language hiding (Exp, Value, Env)
import Trace
import Utils
import Engine hiding (empty)

-- Expects the directives to contain exactly one Predict
simulation :: (MonadRandom m) => Int -> [Directive] -> StateT (Engine m) m [Value]
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
-- (predict (if x x 0.0))
self_select_1 :: [Directive]
self_select_1 =
    [ Assume "x" $ App (Var "bernoulli") []
    , Predict $ v_if (Var "x") (Var "x") 0
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

-- Next subgoal: Daniel says that collapsed exchangeably coupled
-- state, even in the presence of conditionals, does not force
-- regen/detach order symmetry, only detach before regen.  Confirm.
-- - Is is possible that my insertion ordered sets are actually
--   enforcing detach/regen order symmetry?  At least on current
--   examples?

-- Potential goals
-- - Test mem more?
--   - Make sure that I do not leak anything (but especially not memoized
--     SRId entries) under inference with programs involving mem.
-- - Figure out better ways to assess whether inference is producing
--   sensible results (graphical histograms, convergence metrics,
--   comparisons against allegedly equivalent models, etc).
--   - Move my exemplary examples into a fully automated test suite
-- - Do more tests on the interaction between brush, collapsed state,
--   mem, and observations.  Is there anything here besides the
--   (observe (max (normal .) (normal .)) 0) can of bugs?
-- - Massage the code until I can tutor Daniel in it
-- - Understand the set of layers of abstraction of trace operations:
--   - what invariants does each layer preserve?
--   - quickcheck and/or prove preservation of those invariants
--     - do I want versions of layer operations that check their
--       preconditions and throw errors?
--       - e.g., deleteNode can probably do so at an additive log cost
--         by checking whether the node to be deleted is referenced.
--   - find complete sets of operations at each level, so that a higher
--     level does not need to circumvent the level below it
--   - enforce by module export lists that clients do not circumvent
--     those abstraction boundaries.
-- - Implement more inference strategies
--   - Particle methods should be easy because traces are persistent

-- Known bugs:
-- - whether_a_node_is_random_can_change successfully confuses the
--   _randoms field of the Trace, but it is not clear how to get
--   measurably incorrect behavior from this
--   - Presumably the fix would be to insert an approprate
--     isRandomNode check into regenValue somewhere; is a symmetric
--     affordance needed for detach?
-- - self_select_2 (but not self_select_1) leaks (empty) SPRecords
--   (presumably for the lambdas that v_if desugars into)

-- Potential uses for this code
-- - Quasi-independent Venture implemetation for sanity checking
-- - Testbed for clearly stating and checking implementation invariants?
-- - Expository implementation or step in expository implementation path?

-- Non-goals
-- - Latent simulation kernels for SPs
--   - This seems to be the only source of nonzero weights in {regen,detach}Internal
--     (also eval and uneval (detachFamily?))
-- - Absorbing At Applications (I don't even understand the machinery this requires)

-- Daniel's explanation for how to do AAA appears to translate as follows:
-- To cbeta_bernoullii add
--   cbeta_bernoulli_flip (phanY, phanN) (incY, incN) = ... where
--     ctYes = phanY + incY
--     ctNo = phanN + incN
-- etc; also
--   cbeta_bernoulli_log_d_counts :: (phanY, phanN) (incY, incN) = ... -- some double
-- which becomes the weight when detaching or regenning.
-- Daniel says that complexities arise when, e.g., resampling the
-- hyperparameter also causes the set of applications of the made SP to
-- change.

-- Code review topics:
-- - Does all the hair with Uniques make sense, and does it compile away?
