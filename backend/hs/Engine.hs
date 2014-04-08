{-# LANGUAGE TemplateHaskell #-}
{-# LANGUAGE RankNTypes #-}

module Engine where

import Data.Maybe hiding (fromJust)
import qualified Data.Map as M
import Control.Monad.Reader
import Control.Monad.Trans.State.Lazy
import Control.Monad.Random hiding (randoms) -- From cabal install MonadRandom
import Control.Lens  -- from cabal install lens

import Utils
import Language hiding (Exp, Value, Env)
import Trace hiding (empty)
import qualified Trace as T
import Regen
import SP
import Inference

data Engine m =
    Engine { _env :: Env
           , _trace :: (Trace m)
           }

makeLenses ''Engine

empty :: Engine m
empty = Engine Toplevel T.empty

initial :: (MonadRandom m) => Engine m
initial = Engine e t where
  (e, t) = runState (initializeBuiltins Toplevel) T.empty

-- I don't know whether this type signature is as general as possible,
-- but it compiles.
runOn :: (Monad m) => Simple Lens s a -> StateT a m r -> StateT s m r
runOn lens action = do
  value <- use lens
  (result, value') <- lift $ runStateT action value
  lens .= value'
  return result

execOn :: (Monad m) => Simple Lens s a -> StateT a m r -> StateT s m ()
execOn lens action = do
  value <- use lens
  value' <- lift $ execStateT action value
  lens .= value'
  return ()

assume :: (MonadRandom m) => String -> Exp -> (StateT (Engine m) m) ()
assume var exp = do
  -- TODO This implementation of assume does not permit recursive
  -- functions, because of insufficient indirection to the
  -- environment.
  (Engine e _) <- get
  address <- trace `runOn` (eval exp e)
  env %= Frame (M.fromList [(var, address)])

-- Evaluate the expression in the environment (building appropriate
-- structure in the trace), and then constrain its value to the given
-- value (up to chasing down references until a random choice is
-- found).  The constraining appears to consist only in removing that
-- node from the list of random choices.
observe :: (MonadRandom m) => Exp -> Value -> (StateT (Engine m) m) ()
observe exp v = do
  (Engine e _) <- get
  address <- trace `runOn` (eval exp e)
  -- TODO What should happen if one observes a value that had
  -- (deterministic) consequences, e.g.
  -- (assume x (normal 1 1))
  -- (assume y (+ x 1))
  -- (observe x 1)
  -- After this, the trace is presumably in an inconsistent state,
  -- from which it in fact has no way to recover.  As of the present
  -- writing, Venturecxx has this limitation as well, so I will not
  -- address it here.
  trace `execOn` (constrain address v)

predict :: (MonadRandom m) => Exp -> (StateT (Engine m) m) Address
predict exp = do
  (Engine e _) <- get
  trace `runOn` (eval exp e)

data Directive = Assume String Exp
               | Observe Exp Value
               | Predict Exp
  deriving Show

-- Return Just the address of the directive if it's a predict, otherwise Nothing
executeDirective :: (MonadRandom m) => Directive -> StateT (Engine m) m (Maybe Address)
executeDirective (Assume s e) = assume s e >> return Nothing
executeDirective (Observe e v) = observe e v >> return Nothing
executeDirective (Predict e) = predict e >>= return . Just

-- Returns the list of addresses the model wants watched (to wit, the predicts)
execute :: (MonadRandom m) => [Directive] -> StateT (Engine m) m [Address]
execute ds = liftM catMaybes $ mapM executeDirective ds

watching_infer' :: (MonadRandom m) => Address -> Int -> StateT (Trace m) m [Value]
watching_infer' address ct = replicateM ct (do
  modifyM $ metropolis_hastings principal_node_mh
  gets $ fromJust "Value was not restored by inference" . valueOf
         . fromJust "Address became invalid after inference" . (lookupNode address))

watching_infer :: (MonadRandom m) => Address -> Int -> StateT (Engine m) m [Value]
watching_infer address ct = trace `runOn` (watching_infer' address ct)
