{-# LANGUAGE TemplateHaskell #-}

module Engine where

import qualified Data.Map as M
import Control.Monad.Reader
import Control.Monad.Trans.State.Lazy
import Control.Monad.Random hiding (randoms) -- From cabal install MonadRandom
import Control.Lens  -- from cabal install lens

import Language hiding (Exp, Value, Env)
import Trace hiding (empty)
import qualified Trace as T
import Regen

data Engine m =
    Engine { _env :: Env
           , _trace :: (Trace m)
           }

makeLenses ''Engine

empty :: Engine m
empty = Engine Toplevel T.empty

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

