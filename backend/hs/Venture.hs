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
import Utils (fromJust)
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
  lift $ modify $ constrain address v

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
simulation ct ds = liftM head (execute ds) >>= (flip watching_infer ct)

venture_main :: (MonadRandom m) => Int -> [Directive] -> m [Value]
venture_main ct ds = evalStateT (simulation ct ds) empty

-- venture_main 1 $ [Predict $ Datum $ Number 1.0]
-- venture_main 1 $ [Predict $ App (Lam ["x"] (Variable "x")) [(Datum $ Number 1.0)]]
-- (let (id ...) (id 1))
-- venture_main 1 $ [Predict $ App (Lam ["id"] (App (Variable "id") [(Datum $ Number 1.0)])) [(Lam ["x"] (Variable "x"))]]
-- K combinator
-- venture_main 1 $ [Predict $ App (App (Lam ["x"] (Lam ["y"] (Variable "x"))) [(Datum $ Number 1.0)]) [(Datum $ Number 2.0)]]
-- venture_main 10 $ [Predict $ App (Variable "bernoulli") []]
-- venture_main 10 $ [Predict $ App (Variable "normal") [(Datum $ Number 0.0), (Datum $ Number 2.0)]]
-- venture_main 10 $ [Predict $ App (App (Variable "select") [(App (Variable "bernoulli") []), (Lam [] (Datum $ Number 1.0)), (Lam [] (Datum $ Number 2.0))]) []]

chained_normals :: [Directive]
chained_normals =
    [ Assume "x" $ App (Variable "normal") [(Datum $ Number 0.0), (Datum $ Number 2.0)]
    , Assume "y" $ App (Variable "normal") [(Variable "x"), (Datum $ Number 2.0)]
    , Predict $ Variable "y"
    ]

-- venture_main 10 $ chained_normals

observed_chained_normals :: [Directive]
observed_chained_normals =
    [ Assume "x" $ App (Variable "normal") [(Datum $ Number 0.0), (Datum $ Number 2.0)]
    , Assume "y" $ App (Variable "normal") [(Variable "x"), (Datum $ Number 2.0)]
    , Observe (Variable "y") (Number 4.0)
    , Predict $ Variable "x" -- TODO make sure this works with Predict "y" too.
    ]

-- venture_main 10 $ observed_chained_normals


-- Next subgoal: Do MH inference with observations on some trivial
--   programs involving brush

-- Next subgoal: Figure out how to assess whether inference is
--   producing sensible results.

-- Eventual goals
-- - Built-in SPs with collapsed exchangeably coupled state
--   - This imposes the ordering requirement on regen and detach
--   - This is where incorporate and unincorporate (remove) come from

-- Non-goals
-- - Latent simulation kernels for SPs
--   - This seems to be the only source of nonzero weights in {regen,detach}Internal
--     (also eval and uneval (detachFamily?))
-- - Absorbing At Applications (I don't even understand the machinery this requires)
