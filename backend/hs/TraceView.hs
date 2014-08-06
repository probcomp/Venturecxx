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
import Trace hiding (Trace(..), lookupNode, addFreshNode)

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

addFreshNode :: Node -> TraceView m -> (Address, TraceView m)
addFreshNode = undefined

hack_ViewReference :: Address -> (TraceView m) -> Node
hack_ViewReference = undefined

infer :: (MonadRandom m) => Exp -> (StateT (TraceView m) m) ()
infer prog = do
  t <- get
  let t' = extend_trace_view t (t ^. env)
  let inf_exp = App prog [Datum $ hack_ReifiedTraceView t]
  (addr, t'') <- lift $ runStateT (eval inf_exp $ t' ^. env) t'
  put $ hack_ReifiedTraceView' $ fromJust "eval returned empty node" $ valueOf $ fromJust "eval returned invalid address" $ lookupNode addr t''

-- Choice: cut-and-extend at eval or at apply?

-- It doesn't actually matter, because either way, the enclosed trace
-- can read unknown nodes from the enclosing one from the environments
-- contained in closures (or from the immediate lexical environment if
-- it's syntax).  The node representing the extension (be it an
-- extend-apply node or just an extend node) needs (in general) to
-- become a child of all the nodes that it reads.  (Hopefully not all
-- the nodes it could have read?)

-- Here I choose to extend at eval.
-- Eval the "extend" clause of the envisaged new expression grammar.
eval_extend :: (MonadRandom m, MonadTrans t, MonadState (TraceView m) (t m)) => Exp -> Env -> t m Address
eval_extend subexp e = do
  t <- get
  let t' = extend_trace_view t e
  (addr, t'') <- lift $ runStateT (eval subexp $ t' ^. env) t'
  addr' <- state $ addFreshNode (hack_ViewReference addr t'')
  -- Presumably regenNode addr' here to propagate the value
  return addr'
