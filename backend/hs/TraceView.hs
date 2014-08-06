{-# LANGUAGE TemplateHaskell #-}
{-# LANGUAGE FlexibleContexts #-}
{-# LANGUAGE GeneralizedNewtypeDeriving #-}

-- Data structure for extensible traces, which scope inference.

-- Purpose: support directives in procedure bodies, on the way to
-- Venture v1.

module TraceView where

import Control.Lens  -- from cabal install len
import Control.Monad.State -- :set -hide-package monads-tf-0.1.0.1
import Control.Monad.Random -- From cabal install MonadRandom
import qualified Data.Map as M
import Data.Monoid
import qualified Data.Set as S

import Utils
import Trace (SPRecord)

----------------------------------------------------------------------
-- Small objects                                                    --
----------------------------------------------------------------------

data Value = Number Double
           | Symbol String
           | List [Value]
           | Procedure SPAddress
           | Boolean Bool
  deriving (Eq, Ord, Show)

newtype LogDensity = LogDensity Double
    deriving Random

instance Monoid LogDensity where
    mempty = LogDensity 0.0
    (LogDensity x) `mappend` (LogDensity y) = LogDensity $ x + y

log_density_negate :: LogDensity -> LogDensity
log_density_negate (LogDensity x) = LogDensity $ -x

data Exp = Datum Value
         | Var String
         | App Exp [Exp]
         | Lam [String] Exp
  deriving Show

data Env = Toplevel
         | Frame (M.Map String Address) Env
    deriving Show

class Valuable b where
    fromValue :: Value -> Maybe b

instance Valuable Double where
    fromValue (Number d) = Just d
    fromValue _ = Nothing

instance Valuable Bool where
    fromValue (Boolean b) = Just b
    fromValue _ = Nothing

instance Valuable SPAddress where
    fromValue (Procedure a) = Just a
    fromValue _ = Nothing

instance Valuable Value where
    fromValue = Just

newtype Address = Address Unique
    deriving (Eq, Ord, Show)

newtype SPAddress = SPAddress Unique
    deriving (Eq, Ord, Show)

newtype SRId = SRId Unique
    deriving (Eq, Ord, Show)

data SimulationRequest = SimulationRequest SRId Exp Env
    deriving Show

srid :: SimulationRequest -> SRId
srid (SimulationRequest id _ _) = id

----------------------------------------------------------------------
-- Nodes                                                            --
----------------------------------------------------------------------

data Node = Constant Value
          | Reference (Maybe Value) Address
          | Request (Maybe [SimulationRequest]) (Maybe Address) Address [Address]
          | Output (Maybe Value) Address Address [Address] [Address]
    deriving Show

valueOf :: Node -> Maybe Value
valueOf (Constant v) = Just v
valueOf (Reference v _) = v
valueOf (Output v _ _ _ _) = v
valueOf _ = Nothing

----------------------------------------------------------------------
-- Traces                                                           --
----------------------------------------------------------------------

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
  -- The Nodes in t'' will have correct child pointers in t''.  That
  -- means I can compute here which nodes of t this evaluation
  -- actually depends upon, by examining all of the (outward-pointing)
  -- ViewReference nodes in t''.

  -- The right set of parents for the new node is the set of addresses
  -- that the expression read from the enclosing view.
  addr' <- state $ addFreshNode (hack_ViewReference addr t'')
  -- Presumably regenNode addr' here to propagate the value
  return addr'

-- Idea: Implement a RandomDB version of this, with restricted infer.
-- - A TraceFrame has a map from addresses to values and a parent pointer
-- - An environment frame has lexical bindings to addresses, which can be
--   looked up in a trace

-- Choice: One Extend node or two?

-- It seems that if I try to represent the extend syntax with one
-- node, it will have the funny property that resimulating it will
-- change its own dependency list.  That means that come regeneration
-- time, I don't actually know which other nodes I need to be sure to
-- have regenerated before starting to regenerate this one.  Is this
-- the problem that requests were meant to solve for splicing
-- application of compound procedures?  It doesn't work that way here.
-- But I nevertheless can create lookup nodes in the enclosed view and
-- regenerate them -- which may necessitate regenerating nodes in the
-- enclosing view.  That should be fine, however, because that can
-- only happen during resimulation of the enclosed view caused by
-- inference on the enclosing view.  So I choose one node.

-- regenValue_extend :: (MonadRandom m, MonadTrans t, MonadState (TraceView m) (t m)) => Address -> WriterT LogDensity (t m) ()
-- regenValue_extend ... = lift (do

