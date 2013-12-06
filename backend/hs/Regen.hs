module Regen where

import qualified Data.Map as M
import Data.Maybe hiding (fromJust)
import Control.Monad
import Control.Monad.Trans.Writer.Strict
import Control.Monad.Trans.State.Lazy hiding (state)
import Control.Monad.Trans.Class
import Control.Monad.Random -- From cabal install MonadRandom
import Prelude hiding (lookup)
import Control.Lens -- From cabal install lens

import Language hiding (Value, Exp, Env, lookup)
import qualified Language as L
import Trace
import Detach (Scaffold(..))
import qualified InsertionOrderedSet as O
import Utils

regen :: (MonadRandom m) => Scaffold -> Trace m -> WriterT LogDensity m (Trace m)
regen s t = do
  ((_, w), t') <- lift $ runStateT (runWriterT (regen' s)) t
  tell w
  return t'

regen' :: (MonadRandom m) => Scaffold -> WriterT LogDensity (StateT (Trace m) m) ()
regen' Scaffold { drg = d, absorbers = abs } = do
  mapM_ regenNode $ O.toList d
  mapM_ absorbAt $ O.toList abs

regenNode :: (MonadRandom m) => Address -> WriterT LogDensity (StateT (Trace m) m) ()
regenNode a = do
  node <- use $ nodes . hardix "Regenerating a nonexistent node" a
  if isRegenerated node then return ()
  else do
    mapM_ regenNode (parentAddrs node) -- Note that this may change the node at address a
    regenValue a

regenValue :: (MonadRandom m) => Address -> WriterT LogDensity (StateT (Trace m) m) ()
regenValue a = lift (do
  node <- use $ nodes . hardix "Regenerating value for nonexistent node" a
  case node of
    (Constant _) -> return ()
    (Reference _ a') -> do
      node' <- use $ nodes . hardix "Dangling reference found in regenValue" a'
      let v = fromJust "Regenerating value for a reference with non-regenerated referent" $ node' ^. value
      nodes . ix a . value .= Just v
    (Request _ outA opa ps) -> do
      addr <- gets $ fromJust "Regenerating value for a request with no operator" . (chaseOperator opa)
      reqs <- StateT $ runRequester addr ps
      modify $ insertNode a (Request (Just reqs) outA opa ps)
      resps <- evalRequests addr reqs
      case outA of
        Nothing -> return ()
        (Just outA') -> nodes . ix outA' . responses .= resps
    (Output _ reqA opa ps rs) -> do
      SP{ outputter = out } <- gets $ fromJust "Regenerating value for an output with no operator" . (operator node)
      ns <- use nodes
      let args = map (fromJust "Regenerating value for an output with a missing parent" . flip M.lookup ns) ps
      let results = map (fromJust "Regenerating value for an output with a missing request result" . flip M.lookup ns) rs
      v <- lift $ asRandomO out args results
      nodes . ix a . value .= Just v)

evalRequests :: (MonadRandom m) => SPAddress -> [SimulationRequest] -> StateT (Trace m) m [Address]
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
eval :: (MonadRandom m) => Exp -> Env -> StateT (Trace m) m Address
eval (Datum v) _ = state $ addFreshNode $ Constant v
eval (Variable n) e = do
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
  -- Is there a good reason why I don't care about the log density of this regenNode?
  modify $ adjustNode (addOutput addr') addr
  _ <- runWriterT $ regenNode addr'
  return addr'
