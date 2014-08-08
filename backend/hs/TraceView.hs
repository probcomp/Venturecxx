{-# LANGUAGE TemplateHaskell #-}
{-# LANGUAGE FlexibleContexts #-}
{-# LANGUAGE GeneralizedNewtypeDeriving #-}
{-# LANGUAGE MultiParamTypeClasses #-}
{-# LANGUAGE FlexibleInstances #-}
{-# LANGUAGE RankNTypes #-}
{-# LANGUAGE ScopedTypeVariables #-}

-- Data structure for extensible traces, which scope inference.

-- Purpose: support directives in procedure bodies, on the way to
-- Venture v1.

module TraceView where

import Control.Lens  -- from cabal install len
import Control.Monad.Coroutine -- from cabal install monad-coroutine
import qualified Control.Monad.Coroutine.SuspensionFunctors as Susp -- from cabal install monad-coroutine
import Control.Monad.Random -- From cabal install MonadRandom
import Control.Monad.State -- :set -hide-package monads-tf-0.1.0.1
import Control.Monad.Trans.Writer.Strict
import qualified Data.Map as M
import Data.Monoid
import qualified Data.Set as S

import Utils
import Trace (SP, SPRecord)
import Engine (runOn, execOn)

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
           | Body [Statement m] (Exp m)
  deriving Show

data Env = Toplevel
         | Frame (M.Map String Address) Env
  deriving Show

data Statement m = Assume String (Exp m)
                 | Observe (Exp m) (Value m) -- TODO generalize to "constants" read from the environment
                 | Infer (Exp m)
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
              , _parent_view :: Maybe (TraceView rand)
              }
    deriving Show

makeLenses ''TraceView

empty :: TraceView m
empty = TraceView M.empty S.empty M.empty M.empty Nothing

valueAt :: Address -> TraceView m -> Maybe (Value m)
valueAt a t = (t^. nodes . at a) >>= valueOf

fromValueAt :: Valuable m b => Address -> TraceView m -> Maybe b
fromValueAt a t = (t^. nodes . at a) >>= valueOf >>= fromValue

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

extend_trace_view :: (TraceView m) -> Env -> (TraceView m)
extend_trace_view p e = empty { _parent_view = Just p }

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

constrain :: (MonadState (TraceView m) m1) => Address -> (Value m) -> m1 ()
constrain = undefined

----------------------------------------------------------------------
-- Interpreting Venture                                             --
----------------------------------------------------------------------

type RegenEffect m = WriterT LogDensity (StateT (TraceView m) m)
type RequestingValue m = (Susp.Request Address (Value m))
type RegenType m a = Coroutine (RequestingValue m) (RegenEffect m) a
type SuspensionType m a = (Either (RequestingValue m (RegenType m a)) a)

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
eval :: (MonadRandom m) => Exp m -> Env -> RegenEffect m Address
eval (Datum v) _ = state $ addFreshNode $ Constant v
eval (Var n) e = do
  let answer = case env_lookup n e of
                 Nothing -> error $ "Unbound variable " ++ show n
                 (Just a) -> Reference Nothing a
  addr <- state $ addFreshNode answer
  _ <- regenNode addr
  return addr
eval (Lam vs exp) e = do
  spAddr <- state $ addFreshSP $ compoundSP vs exp e
  state $ addFreshNode $ Constant $ Procedure spAddr
eval (App op args) env = do
  op' <- eval op env
  args' <- sequence $ map (flip eval env) args
  addr <- state $ addFreshNode (Request Nothing Nothing op' args')
  _ <- regenNode addr
  reqAddrs <- gets $ fulfilments addr
  addr' <- state $ addFreshNode (Output Nothing addr op' args' reqAddrs)
  nodes . ix addr . out_node .= Just addr'
  _ <- regenNode addr'
  return addr'
eval (Ext exp) e = do
  addr <- state $ addFreshNode (Extension Nothing exp e [])
  _ <- regenNode addr
  return addr
-- TODO If begin is really supposed to splice into the enclosing
-- environment, then eval must be able to modify the environment it is
-- running in.
eval (Body stmts exp) e = do
  t <- get
  (t', e') <- lift $ lift $ execStateT (mapM_ exec stmts) (t, e)
  put t'
  eval exp e'

regenNode :: (MonadRandom m) => Address -> WriterT LogDensity (StateT (TraceView m) m) (Value m)
regenNode a = do
  node <- use $ nodes . hardix "Regenerating a nonexistent node" a
  if isRegenerated node then return $ fromJust "foo" $ valueOf node
  else do
    mapM_ regenNode (parentAddrs node) -- Note that this may change the node at address a
    regenValueNoCoroutine a

regenValueNoCoroutine :: (MonadRandom m) => Address -> WriterT LogDensity (StateT (TraceView m) m) (Value m)
regenValueNoCoroutine a = lift (do -- Should be able to produce weight in principle, but current SPs do not.
  node <- use $ nodes . hardix "Regenerating value for nonexistent node" a
  case node of
    (Constant v) -> return v
    (Reference _ _) -> error "References are handled by regenValue directly"
    (Request _ outA opa ps) -> do
      addr <- gets $ fromJust "Regenerating value for a request with no operator" . (fromValueAt opa)
      reqs <- runRequester addr ps
      nodes . ix a . sim_reqs .= Just reqs
      resps <- evalRequests addr reqs
      do_incorporateR a
      case outA of
        Nothing -> return ()
        (Just outA') -> responsesAt outA' .= resps
      return undefined
    (Output _ _ opa ps rs) -> do
      addr <- gets $ fromJust "Regenerating value for an output with no operator" . (fromValueAt opa)
      v <- runOutputter addr ps rs
      nodes . ix a . value .= Just v
      do_incorporate a
      return v
    (Extension _ _ _ _) -> error "Extensions are handled by regenValue directly")

runRegenEffect :: RegenEffect m a -> (TraceView m) -> m ((a, LogDensity), (TraceView m))
runRegenEffect act t = runStateT (runWriterT act) t

coroutineRunRegenEffect :: (Monad m) => RegenType m a -> LogDensity -> (TraceView m) -> Coroutine (RequestingValue m) m ((a, LogDensity), (TraceView m))
coroutineRunRegenEffect c d t = Coroutine act where
    act = do
      ((res, density), t') <- runRegenEffect (resume c) t
      case res of
        Right result -> return $ Right ((result, d `mappend` density), t')
        Left susp -> return $ Left $ fmap (\c' -> coroutineRunRegenEffect c' (d `mappend` density) t') susp

regenNode' :: (MonadRandom m) => Address -> RegenType m (Value m)
regenNode' a = do
  t <- lift get
  case lookupNode a t of
    (Just node) -> if isRegenerated node then return $ fromJust "foo" $ valueOf node
                   else do
                     mapM_ regenNode' (parentAddrs node) -- Note that this may change the node at address a
                     regenValue a
    Nothing -> Susp.request a

regenValue :: (MonadRandom m) => Address -> RegenType m (Value m)
regenValue a = do
  node <- lift (use $ nodes . hardix "Regenerating value for nonexistent node" a)
  case node of
    (Reference _ a') -> do
      v <- lookupMaybeRequesting a'
      lift (nodes . ix a . value .= Just v)
      return v
    (Extension _ exp e _) -> do
      t <- lift get
      (v, density, requested, new_trace) <- mapMonad (lift . lift) $ manage_subregen exp e t
      lift $ tell density
      lift $ put new_trace
      lift (nodes . ix a . undefined .= reverse requested)
      lift (nodes . ix a . value .= Just v)
      return v
    _ -> lift $ regenValueNoCoroutine a

manage_subregen :: forall m. (MonadRandom m) => Exp m -> Env -> TraceView m -> Coroutine (RequestingValue m) m (Value m, LogDensity, [Address], TraceView m)
manage_subregen exp e t = do
  (((addr, inner_density), inner_t'), (density, requested, t')) <- foldRunMC handle_regeneration_request (mempty, [], t) subregen'
  let v = fromJust "Subevaluation yielded no value" $ valueAt addr inner_t'
  return (v, density, requested, t') -- TODO What to do with the inner density?
    where
      inner_t = extend_trace_view t e
      subregen :: RegenType m Address
      subregen = eval' exp e
      subregen' :: Coroutine (RequestingValue m) m ((Address, LogDensity), (TraceView m))
      subregen' = coroutineRunRegenEffect subregen mempty inner_t

lookupMaybeRequesting :: (MonadRandom m) => Address -> RegenType m (Value m)
lookupMaybeRequesting a = do
  t <- lift get
  case lookupNode a t of
    (Just node') -> return $ fromJust "Regenerating value for a reference with non-regenerated referent" $ node' ^. value
    Nothing -> Susp.request a

handle_regeneration_request :: (MonadRandom m) => (LogDensity, [Address], TraceView m) ->
                               (RequestingValue m (Coroutine (RequestingValue m) m
                                                             ((Address, LogDensity), (TraceView m)))) ->
                               Coroutine (RequestingValue m) m (Coroutine (RequestingValue m) m
                                                                          ((Address, LogDensity), (TraceView m))
                                                               , (LogDensity, [Address], TraceView m))
handle_regeneration_request (d, as, t) (Susp.Request addr k) = do
  ((v, d'), t') <- coroutineRunRegenEffect (regenNode' addr) d t
  return (k v, (d', (addr:as), t'))

eval' :: (MonadRandom m) => Exp m -> Env -> RegenType m Address
eval' = undefined

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

exec :: (MonadRandom m) => Statement m -> StateT ((TraceView m), Env) m ()
exec (Assume var exp) = do
  -- TODO This implementation of assume does not permit recursive
  -- functions, because of insufficient indirection to the
  -- environment.
  e <- gets snd
  (address, density) <- _1 `runOn` (runWriterT $ eval exp e)
  -- TODO Carry the density
  _2 %= Frame (M.fromList [(var, address)])
  return ()
exec (Observe exp v) = do
  e <- gets snd
  (address, density) <- _1 `runOn` (runWriterT $ eval exp e)
  -- TODO Carry the density
  -- TODO What should happen if one observes a value that had
  -- (deterministic) consequences, e.g.
  -- (assume x (normal 1 1))
  -- (assume y (+ x 1))
  -- (observe x 1)
  -- After this, the trace is presumably in an inconsistent state,
  -- from which it in fact has no way to recover.  Venturecxx invokes
  -- a complicated operation to fix this, which I should probably
  -- port.
  _1 `execOn` (constrain address v)
exec (Infer _) = error "Infer should be handled by exec'"

exec' :: (MonadRandom m) => Statement m -> Coroutine (RequestingValue m) (StateT ((TraceView m), Env) m) ()
exec' (Infer prog) = do
  (t, e) <- lift get
  let t' = extend_trace_view t e
  let inf_exp = App prog [Datum $ ReifiedTraceView t]
  -- Is the view t itself fully regenerated here?  Do I need to be
  -- able to intercept regeneration requests?  Do I need to be able to
  -- update the reified view!?
  -- Can exec' ever be called inside a regen' without an intervening
  -- extend?  I think so.  If that is the case, then it may happen
  -- that some nodes in the current view are not yet regenerated.  If
  -- that, in turn, is the case, then the enclosed eval' of the
  -- inf_exp may uncover new dependencies on such unregenerated
  -- values, in which case it will be necessary to regenerate them.
  -- TODO: Make that happen, or arrange for it not to be an issue.
  -- Note: if the reified trace can be under-regenerated, then SPs
  -- need to be able to suspend themselves in order to request further
  -- regeneration.
  ((addr, d), t'') <- mapMonad lift $ coroutineRunRegenEffect (eval' inf_exp e) mempty t'
  let ReifiedTraceView t''' = fromJust "eval returned empty node" $ valueOf $ fromJust "eval returned invalid address" $ lookupNode addr t''
  -- TODO What do I do with the density coming up from the bottom, if any?
  lift (_1 .= t''')
exec' s = lift $ exec s
