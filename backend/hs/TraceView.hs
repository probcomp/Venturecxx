{-# LANGUAGE TemplateHaskell #-}
{-# LANGUAGE FlexibleContexts #-}
{-# LANGUAGE GeneralizedNewtypeDeriving #-}
{-# LANGUAGE MultiParamTypeClasses #-}
{-# LANGUAGE FlexibleInstances #-}
{-# LANGUAGE RankNTypes #-}

-- Data structure for extensible traces, which scope inference.

-- Purpose: support directives in procedure bodies, on the way to
-- Venture v1.

module TraceView where

import Control.Lens  -- from cabal install len
import Control.Monad.Random -- From cabal install MonadRandom
import Control.Monad.State -- :set -hide-package monads-tf-0.1.0.1
import Control.Monad.Trans.Writer.Strict
import qualified Data.Map as M
import Data.Monoid
import qualified Data.Set as S

import Utils
import Trace (SP, SPRecord)

----------------------------------------------------------------------
-- Small objects                                                    --
----------------------------------------------------------------------

data Value m = Number Double
             | Symbol String
             | List [Value m]
             | Procedure SPAddress
             | ReifiedTraceView (TraceView m)
             | Boolean Bool
  deriving Show

newtype LogDensity = LogDensity Double
    deriving Random

instance Monoid LogDensity where
    mempty = LogDensity 0.0
    (LogDensity x) `mappend` (LogDensity y) = LogDensity $ x + y

log_density_negate :: LogDensity -> LogDensity
log_density_negate (LogDensity x) = LogDensity $ -x

data Exp m = Datum (Value m)
           | Var String
           | App (Exp m) [Exp m]
           | Lam [String] (Exp m)
           | Ext (Exp m)
  deriving Show

data Env = Toplevel
         | Frame (M.Map String Address) Env
    deriving Show

env_lookup :: String -> Env -> Maybe Address
env_lookup = undefined

class Valuable m b where
    fromValue :: Value m -> Maybe b

instance Valuable m Double where
    fromValue (Number d) = Just d
    fromValue _ = Nothing

instance Valuable m Bool where
    fromValue (Boolean b) = Just b
    fromValue _ = Nothing

instance Valuable m SPAddress where
    fromValue (Procedure a) = Just a
    fromValue _ = Nothing

instance Valuable m (Value m) where
    fromValue v = Just v

newtype Address = Address Unique
    deriving (Eq, Ord, Show)

newtype SPAddress = SPAddress Unique
    deriving (Eq, Ord, Show)

newtype SRId = SRId Unique
    deriving (Eq, Ord, Show)

data SimulationRequest m = SimulationRequest SRId (Exp m) Env
    deriving Show

srid :: SimulationRequest m -> SRId
srid (SimulationRequest id _ _) = id

----------------------------------------------------------------------
-- Nodes                                                            --
----------------------------------------------------------------------

data Node m = Constant (Value m)
            | Reference (Maybe (Value m)) Address
            | Request (Maybe [SimulationRequest m]) (Maybe Address) Address [Address]
            | Output (Maybe (Value m)) Address Address [Address] [Address]
            | Extension (Maybe (Value m)) (Exp m) Env [Address]
  deriving Show

valueOf :: Node m -> Maybe (Value m)
valueOf (Constant v) = Just v
valueOf (Reference v _) = v
valueOf (Output v _ _ _ _) = v
valueOf _ = Nothing

value :: Simple Lens (Node m) (Maybe (Value m))
value = lens valueOf undefined

isRegenerated :: Node m -> Bool
isRegenerated (Constant _) = True
isRegenerated (Reference Nothing _) = False
isRegenerated (Reference (Just _) _) = True
isRegenerated (Request Nothing _ _ _) = False
isRegenerated (Request (Just _) _ _ _) = True
isRegenerated (Output Nothing _ _ _ _) = False
isRegenerated (Output (Just _) _ _ _ _) = True
isRegenerated (Extension Nothing _ _ _) = False
isRegenerated (Extension (Just _) _ _ _) = True

sim_reqs :: Simple Lens (Node m) (Maybe [SimulationRequest m])
sim_reqs = undefined

parentAddrs :: Node m -> [Address]
parentAddrs (Constant _) = []
parentAddrs (Reference _ addr) = [addr]
parentAddrs (Request _ _ a as) = a:as
parentAddrs (Output _ reqA a as as') = reqA:a:(as ++ as')
parentAddrs (Extension _ _ _ as) = as

----------------------------------------------------------------------
-- Traces                                                           --
----------------------------------------------------------------------

data TraceView rand =
    TraceView { _nodes :: M.Map Address (Node rand)
              , _randoms :: S.Set Address -- Really scopes, but ok
              , _node_children :: M.Map Address (S.Set Address)
              , _sprs :: M.Map SPAddress (SPRecord rand)
              , _env :: Env
              }
    deriving Show

makeLenses ''TraceView

fromValueAt :: Valuable m b => Address -> TraceView m -> Maybe b
fromValueAt a t = (t^. nodes . at a) >>= valueOf >>= fromValue

assume :: (MonadRandom m) => String -> Exp m -> (StateT (TraceView m) m) Address
assume var exp = do
  -- TODO This implementation of assume does not permit recursive
  -- functions, because of insufficient indirection to the
  -- environment.
  e <- use env
  address <- (eval exp e)
  env %= Frame (M.fromList [(var, address)])
  return address

extend_trace_view :: (TraceView m) -> Env -> (TraceView m)
extend_trace_view = undefined

lookupNode :: Address -> (TraceView m) -> Maybe (Node m)
lookupNode = undefined

addFreshNode :: Node m -> TraceView m -> (Address, TraceView m)
addFreshNode = undefined

addFreshSP :: SP m -> TraceView m -> (SPAddress, TraceView m)
addFreshSP = undefined

out_node :: Simple Setter (Node m) (Maybe Address)
out_node = undefined

compoundSP :: (Monad m) => [String] -> Exp m -> Env -> SP m
compoundSP = undefined

responsesAt :: Address -> Simple Lens (TraceView m) [Address]
responsesAt = undefined

----------------------------------------------------------------------
-- Advanced Trace Manipulations                                     --
----------------------------------------------------------------------

runRequester :: (Monad m, MonadTrans t, MonadState (TraceView m) (t m)) =>
                SPAddress -> [Address] -> t m [SimulationRequest m]
runRequester = undefined

runOutputter :: (Monad m, MonadTrans t, MonadState (TraceView m) (t m)) =>
                SPAddress -> [Address] -> [Address] -> t m (Value m)
runOutputter = undefined

fulfilments :: Address -> TraceView m -> [Address]
fulfilments = undefined

do_incorporate :: (MonadState (TraceView m) m1) => Address -> m1 ()
do_incorporate = undefined

do_incorporateR :: (MonadState (TraceView m) m1) => Address -> m1 ()
do_incorporateR = undefined

hack_ViewReference :: Address -> (TraceView m) -> Node m
hack_ViewReference = undefined

infer :: (MonadRandom m) => Exp m -> (StateT (TraceView m) m) ()
infer prog = do
  t <- get
  let t' = extend_trace_view t (t ^. env)
  let inf_exp = App prog [Datum $ ReifiedTraceView t]
  (addr, t'') <- lift $ runStateT (eval inf_exp $ t' ^. env) t'
  let ReifiedTraceView t''' = fromJust "eval returned empty node" $ valueOf $ fromJust "eval returned invalid address" $ lookupNode addr t''
  put t'''

evalRequests :: (MonadRandom m) => SPAddress -> [SimulationRequest m] -> StateT (TraceView m) m [Address]
evalRequests = undefined

-- Choice: cut-and-extend at eval or at apply?

-- It doesn't actually matter, because either way, the enclosed trace
-- can read unknown nodes from the enclosing one from the environments
-- contained in closures (or from the immediate lexical environment if
-- it's syntax).  The node representing the extension (be it an
-- extend-apply node or just an extend node) needs (in general) to
-- become a child of all the nodes that it reads.  (Hopefully not all
-- the nodes it could have read?)

-- Here I choose to extend at eval.
-- Returns the address of the fresh node holding the result of the
-- evaluation.
eval :: (MonadRandom m) => Exp m -> Env -> StateT (TraceView m) m Address
eval (Datum v) _ = state $ addFreshNode $ Constant v
eval (Var n) e = do
  let answer = case env_lookup n e of
                 Nothing -> error $ "Unbound variable " ++ show n
                 (Just a) -> Reference Nothing a
  addr <- state $ addFreshNode answer
  -- Is there a good reason why I don't care about the log density of this regenNode?
  _ <- runWriterT $ regenNode addr
  return addr
eval (Lam vs exp) e = do
  spAddr <- state $ addFreshSP $ compoundSP vs exp e
  state $ addFreshNode $ Constant $ Procedure spAddr
eval (App op args) env = do
  op' <- eval op env
  args' <- sequence $ map (flip eval env) args
  addr <- state $ addFreshNode (Request Nothing Nothing op' args')
  -- Is there a good reason why I don't care about the log density of this regenNode?
  _ <- runWriterT $ regenNode addr
  reqAddrs <- gets $ fulfilments addr
  addr' <- state $ addFreshNode (Output Nothing addr op' args' reqAddrs)
  nodes . ix addr . out_node .= Just addr'
  -- Is there a good reason why I don't care about the log density of this regenNode?
  _ <- runWriterT $ regenNode addr'
  return addr'
eval (Ext exp) e = do
  addr <- state $ addFreshNode (Extension Nothing exp e [])
  -- Is there a good reason why I don't care about the log density of this regenNode?
  _ <- runWriterT $ regenNode addr
  return addr

regenNode :: (MonadRandom m) => Address -> WriterT LogDensity (StateT (TraceView m) m) ()
regenNode a = do
  node <- use $ nodes . hardix "Regenerating a nonexistent node" a
  if isRegenerated node then return ()
  else do
    mapM_ regenNode (parentAddrs node) -- Note that this may change the node at address a
    regenValue a

regenValue :: (MonadRandom m) => Address -> WriterT LogDensity (StateT (TraceView m) m) ()
regenValue a = lift (do
  node <- use $ nodes . hardix "Regenerating value for nonexistent node" a
  case node of
    (Constant _) -> return ()
    (Reference _ a') -> do
      node' <- use $ nodes . hardix "Dangling reference found in regenValue" a'
      let v = fromJust "Regenerating value for a reference with non-regenerated referent" $ node' ^. value
      nodes . ix a . value .= Just v
    (Request _ outA opa ps) -> do
      addr <- gets $ fromJust "Regenerating value for a request with no operator" . (fromValueAt opa)
      reqs <- runRequester addr ps
      nodes . ix a . sim_reqs .= Just reqs
      resps <- evalRequests addr reqs
      do_incorporateR a
      case outA of
        Nothing -> return ()
        (Just outA') -> responsesAt outA' .= resps
    (Output _ _ opa ps rs) -> do
      addr <- gets $ fromJust "Regenerating value for an output with no operator" . (fromValueAt opa)
      v <- runOutputter addr ps rs
      nodes . ix a . value .= Just v
      do_incorporate a)

eval_extend :: (MonadRandom m, MonadTrans t, MonadState (TraceView m) (t m)) => Exp m -> Env -> t m Address
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

