module Venture where

import Data.Maybe hiding (fromJust)
import qualified Data.Map as M
import Control.Monad.Reader
import Control.Monad.Trans.State.Lazy
import Control.Monad.Random hiding (randoms) -- From cabal install MonadRandom

import Language hiding (Exp, Value, Env)
import Trace
import Regen
import SP
import Utils
import Inference

data Directive = Assume String Exp
               | Observe Exp Value
               | Predict Exp

assume :: (MonadRandom m) => String -> Exp -> StateT Env (StateT (Trace m) m) ()
assume var exp = do
  -- TODO This implementation of assume does not permit recursive
  -- functions, because of insufficient indirection to the
  -- environment.
  env <- get
  address <- lift $ eval exp env
  modify $ Frame (M.fromList [(var, address)])

-- Evaluate the expression in the environment (building appropriate
-- structure in the trace), and then constrain its value to the given
-- value (up to chasing down references until a random choice is
-- found).  The constraining appears to consist only in removing that
-- node from the list of random choices.
observe :: (MonadRandom m) => Exp -> Value -> ReaderT Env (StateT (Trace m) m) ()
observe exp v = do
  env <- ask
  address <- lift $ eval exp env
  -- TODO What should happen if one observes a value that had
  -- (deterministic) consequences, e.g.
  -- (assume x (normal 1 1))
  -- (assume y (+ x 1))
  -- (observe x 1)
  -- After this, the trace is presumably in an inconsistent state,
  -- from which it in fact has no way to recover.  As of the present
  -- writing, Venturecxx has this limitation as well, so I will not
  -- address it here.
  lift $ constrain address v

predict :: (MonadRandom m) => Exp -> ReaderT Env (StateT (Trace m) m) Address
predict exp = do
  env <- ask
  lift $ eval exp env

-- Returns the list of addresses the model wants watched
execute :: (MonadRandom m) => [Directive] -> StateT (Trace m) m [Address]
execute ds = evalStateT (do
  modifyM initializeBuiltins
  liftM catMaybes $ mapM executeOne ds) Toplevel where
    -- executeOne :: Directive -> StateT Env (StateT (Trace m) m) (Maybe Address)
    executeOne (Assume s e) = assume s e >> return Nothing
    executeOne (Observe e v) = get >>= lift . runReaderT (observe e v) >> return Nothing
    executeOne (Predict e) = get >>= lift . runReaderT (predict e) >>= return . Just


watching_infer :: (MonadRandom m) => Address -> Int -> StateT (Trace m) m [Value]
watching_infer address ct = replicateM ct (do
  modifyM $ metropolis_hastings principal_node_mh
  gets $ fromJust "Value was not restored by inference" . valueOf
         . fromJust "Address became invalid after inference" . (lookupNode address))

-- Expects the directives to contain exactly one Predict
simulation :: (MonadRandom m) => Int -> [Directive] -> StateT (Trace m) m [Value]
simulation ct ds = do
  target <- liftM head (execute ds)
  watching_infer target ct

venture_main :: (MonadRandom m) => Int -> [Directive] -> m [Value]
venture_main ct ds = evalStateT (simulation ct ds) empty

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
condition_on_flip = [Predict $ App (App (Var "select") [(App (Var "bernoulli") []), (Lam [] 1), (Lam [] 2)]) []]
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

-- Next subgoal: Daniel says that collapsed exchangeably coupled
-- state, even in the presence of conditionals, does not force
-- regen/detach order symmetry, only detach before regen.  Confirm.

-- Eventual goals
-- - Built-in SPs with collapsed exchangeably coupled state
--   - This is where incorporate and unincorporate (remove) come from
--   - In the presence of conditionals, does this impose the ordering
--     requirement on regen and detach or merely force detach to
--     precede regen?

-- Potential goals
-- - Implement and test mem
-- - Figure out better ways to assess whether inference is producing
--   sensible results (graphical histograms, convergence metrics,
--   comparisons against allegedly equivalent models, etc).
-- - Do MH inference with observations on some trivial programs
--   involving brush.  Is there anything here besides the
--   (observe (max (normal .) (normal .)) 0) can of bugs?
-- - Massage the code until I can tutor Daniel in it
-- - Understand the set of layers of abstraction of trace operations:
--   - what invariants does each layer preserve?
--   - quickcheck and/or prove preservation of those invariants
--   - enforce by module export lists that clients do not circumvent
--     those abstraction boundaries.
-- - Implement more inference strategies
--   - Particle methods should be easy because traces are persistent

-- Potential uses for this code
-- - Quasi-independent Venture implemetation for sanity checking
-- - Testbed for clearly stating and checking implementation invariants?
-- - Expository implementation or step in expository implementation path?

-- Non-goals
-- - Latent simulation kernels for SPs
--   - This seems to be the only source of nonzero weights in {regen,detach}Internal
--     (also eval and uneval (detachFamily?))
-- - Absorbing At Applications (I don't even understand the machinery this requires)
