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

import Utils
import Language hiding (Value, Exp, Env)
import Trace hiding (Trace(..), lookupNode)

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

hack_ReifiedTraceView :: (TraceView m) -> Value
hack_ReifiedTraceView = undefined

hack_ReifiedTraceView' :: Value -> (TraceView m)
hack_ReifiedTraceView' = undefined

extend_trace_view :: (TraceView m) -> Env -> (TraceView m)
extend_trace_view = undefined

lookupNode :: Address -> (TraceView m) -> Maybe Node
lookupNode = undefined

infer :: (MonadRandom m) => Exp -> (StateT (TraceView m) m) ()
infer prog = do
  t <- get
  let t' = extend_trace_view t (t ^. env)
  let inf_exp = App prog [Datum $ hack_ReifiedTraceView t]
  (addr, t'') <- lift $ runStateT (eval inf_exp $ t' ^. env) t'
  put $ hack_ReifiedTraceView' $ fromJust "eval returned empty node" $ valueOf $ fromJust "eval returned invalid address" $ lookupNode addr t''
