{-# LANGUAGE TemplateHaskell #-}
{-# LANGUAGE FlexibleContexts #-}

-- Data structure for extensible traces, which scope inference.

-- Purpose: support directives in procedure bodies, on the way to
-- Venture v1.

module TraceView where

import qualified Data.Map as M
import qualified Data.Set as S
import Control.Lens  -- from cabal install len
import Control.Monad.State -- :set -hide-package monads-tf-0.1.0.1
import Control.Monad.Random -- From cabal install MonadRandom

import Language hiding (Value, Exp, Env)
import Trace hiding (Trace(..))

data TraceView rand =
    TraceView { _nodes :: M.Map Address Node
              , _randoms :: S.Set Address -- Really scopes, but ok
              , _node_children :: M.Map Address (S.Set Address)
              , _sprs :: M.Map SPAddress (SPRecord rand)
              , _env :: Env
              }
    deriving Show

makeLenses ''TraceView


eval :: (MonadRandom m, MonadTrans t, MonadState (TraceView m) (t m)) => Exp -> Env -> t m Address
eval = undefined

assume :: (MonadRandom m) => String -> Exp -> (StateT (TraceView m) m) Address
assume var exp = do
  -- TODO This implementation of assume does not permit recursive
  -- functions, because of insufficient indirection to the
  -- environment.
  e <- use env
  address <- (eval exp e)
  env %= Frame (M.fromList [(var, address)])
  return address
