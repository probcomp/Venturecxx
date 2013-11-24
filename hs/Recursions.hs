module Recursions where

import qualified Data.Map as M
import Data.Maybe
import Control.Monad
import Control.Monad.Trans.Writer.Strict
import Control.Monad.Trans.State.Lazy hiding (state)
import Control.Monad.Trans.Class
import Control.Monad.Random -- From cabal install MonadRandom
import Prelude hiding (lookup)

import Language hiding (Value, Exp, Env, lookup)
import qualified Language as L
import Trace

regen :: (MonadRandom m) => Trace m -> WriterT LogDensity m (Trace m)
regen = undefined

regenNode :: (MonadRandom m) => Address -> WriterT LogDensity (StateT (Trace m) m) ()
regenNode a = do
  node <- lift $ gets $ fromJust . (lookupNode a)
  if isRegenerated node then return ()
  else do
    mapM_ regenNode (parentAddrs node)
    regenValue a

regenValue :: (MonadRandom m) => Address -> WriterT LogDensity (StateT (Trace m) m) ()
regenValue a = lift (do
  node <- gets $ fromJust . (lookupNode a)
  case node of
    (Constant _) -> return ()
    (Reference _ a') -> do
      t <- get
      let v = fromJust ( (lookupNode a' t) >>= valueOf )
      modify $ insertNode a (Reference (Just v) a')
    (Request _ opa ps) -> do
      addr <- gets $ fromJust . (chaseOperator opa)
      reqs <- StateT $ runRequester addr ps
      modify $ insertNode a (Request (Just reqs) opa ps)
      addr <- gets $ fromJust . (operatorAddr node)
      evalRequests addr reqs
    (Output _ opa ps rs) -> do
      SP{ outputter = out } <- gets $ fromJust . (operator node)
      ns <- gets nodes
      let args = map (fromJust . flip M.lookup ns) ps
      let results = map (fromJust . flip M.lookup ns) rs
      v <- lift $ out args results
      modify $ insertNode a (Output (Just v) opa ps rs))

evalRequests :: (MonadRandom m) => SPAddress -> [SimulationRequest] -> StateT (Trace m) m ()
evalRequests a srs = mapM_ evalRequest srs where
    evalRequest (SimulationRequest id exp env) = do
      isCached <- gets $ isJust . (lookupResponse a id)
      if isCached then return ()
      else do
        addr <- eval exp env
        modify $ insertResponse a id addr

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
  addr <- state $ addFreshNode (Request Nothing op' args')
  -- Is there a good reason why I don't care about the log density of this regenNode?
  _ <- runWriterT $ regenNode addr
  reqAddrs <- gets $ fulfilments addr
  addr' <- state $ addFreshNode (Output Nothing op' args' reqAddrs)
  -- Is there a good reason why I don't care about the log density of this regenNode?
  _ <- runWriterT $ regenNode addr'
  return addr'
