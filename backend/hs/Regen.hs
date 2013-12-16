{-# LANGUAGE FlexibleContexts, DoAndIfThenElse #-}

module Regen where

import Data.Maybe hiding (fromJust)
import Control.Monad
import Control.Monad.Trans.Writer.Strict
import Control.Monad.Trans.State.Lazy hiding (state, gets, modify)
import Control.Monad.Trans.Class
import Control.Monad.State.Class
import Control.Monad.Random -- From cabal install MonadRandom
import Prelude hiding (lookup)
import Control.Lens -- From cabal install lens

import Language hiding (Value, Exp, Env, lookup)
import qualified Language as L
import Trace
import Detach (Scaffold(..))
import qualified InsertionOrderedSet as O
import Utils
import SP (compoundSP)

regen :: (MonadRandom m) => Scaffold -> Trace m -> WriterT LogDensity m (Trace m)
regen s t = do
  ((_, w), t') <- lift $ runStateT (runWriterT (regen' s)) t
  tell w
  return t'

regen' :: (MonadRandom m) => Scaffold -> WriterT LogDensity (StateT (Trace m) m) ()
regen' Scaffold { _drg = d, _absorbers = abs } = do
  mapM_ regenNode $ O.toList d
  mapM_ absorbAt $ O.toList abs

regenNode :: (MonadRandom m, MonadTrans t, MonadState (Trace m) (t m)) => Address -> WriterT LogDensity (t m) ()
regenNode a = do
  node <- use $ nodes . hardix "Regenerating a nonexistent node" a
  if isRegenerated node then return ()
  else do
    mapM_ regenNode (parentAddrs node) -- Note that this may change the node at address a
    regenValue a

regenValue :: (MonadRandom m, MonadTrans t, MonadState (Trace m) (t m)) => Address -> WriterT LogDensity (t m) ()
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

evalRequests :: (MonadRandom m, MonadTrans t, MonadState (Trace m) (t m)) => SPAddress -> [SimulationRequest] -> t m [Address]
evalRequests a srs = mapM evalRequest srs where
    evalRequest (SimulationRequest id exp env) = do
      cached <- gets $ lookupResponse a id
      case cached of
        (Just addr) -> return addr
        Nothing -> do
          addr <- eval exp env
          modify $ insertResponse a id addr
          return addr

-- Returns the address of the fresh node holding the result of the
-- evaluation.
eval :: (MonadRandom m, MonadTrans t, MonadState (Trace m) (t m)) => Exp -> Env -> t m Address
eval (Datum v) _ = state $ addFreshNode $ Constant v
eval (Var n) e = do
  let answer = case L.lookup n e of
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
