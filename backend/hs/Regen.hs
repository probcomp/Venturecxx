{-# LANGUAGE FlexibleContexts, DoAndIfThenElse #-}
{-# LANGUAGE ConstraintKinds #-}

module Regen where

import Data.Foldable
import Data.Functor.Compose
import Data.Map (Map)
import qualified Data.Map as Map
import Data.Maybe hiding (fromJust)
import Control.Monad hiding (mapM_)
import Control.Monad.Trans.Writer.Strict
import Control.Monad.Trans.State.Strict hiding (state, get, gets, modify)
import Control.Monad.Trans.Class
import Control.Monad.State.Class
import Control.Monad.Random -- From cabal install MonadRandom
import Prelude hiding (lookup, mapM_)
import Control.Lens -- From cabal install lens

import Language hiding (Value, Exp, Env, lookup)
import qualified Language as L
import Trace
import Subproblem (Scaffold(..))
import qualified InsertionOrderedSet as O
import Utils
import SP (compoundSP)

-- If the emitted LogDensity is the importance weight of the returned
-- proposal against the prior at each node, then regen will return the
-- importance weight of the whole proposal against the local
-- posterior.
-- Separate the SP case in the type because SPs require special
-- handling (namely, making SP records).  This is a crock.
type Proposal m num = Address -> Trace m num ->
    Writer (LogDensity num) (Either (m (Value num)) (SP m))

regen :: (MonadRandom m, Numerical num) => Scaffold -> Proposal m num -> Trace m num ->
         WriterT (LogDensity num) m (Trace m num)
regen s propose t = do
  ((_, w), t') <- lift $ runStateT (runWriterT (regen' s propose)) t
  tell w
  return t'

regen' :: (MonadRandom m, Numerical num) => Scaffold -> Proposal m num ->
          WriterT (LogDensity num) (StateT (Trace m num) m) ()
regen' Scaffold { _drg = d, _absorbers = abs } propose = do
  mapM_ (regenNode propose) $ O.toList d
  mapM_ absorbAt $ O.toList abs

regenNode :: (MonadRandom m, MonadTrans t, MonadState (Trace m num) (t m), Numerical num) =>
             Proposal m num -> Address -> WriterT (LogDensity num) (t m) ()
regenNode propose a = do
  node <- use $ nodes . hardix "Regenerating a nonexistent node" a
  if isRegenerated node then return ()
  else do
    -- Note that this may change the node at address a
    mapM_ (regenNode propose) (parentAddrs node)
    regenValue propose a

regenValue :: (MonadRandom m, MonadTrans t, MonadState (Trace m num) (t m), Numerical num) =>
              Proposal m num -> Address -> WriterT (LogDensity num) (t m) ()
regenValue propose a = do
  node <- use $ nodes . hardix "Regenerating value for nonexistent node" a
  case node of
    (Constant _) -> return ()
    (Reference _ a') -> lift (do
      node' <- use $ nodes . hardix "Dangling reference found in regenValue" a'
      let v = fromJust "Regenerating value for a reference with non-regenerated referent" $ node' ^. value
      nodes . ix a . value .= Just v)
    (Request _ outA opa ps) -> lift (do
      addr <- gets $ fromJust "Regenerating value for a request with no operator" . (fromValueAt opa)
      reqs <- runRequester addr ps -- TODO allow proposals to tweak requests?
      nodes . ix a . sim_reqs .= Just reqs
      resps <- evalRequests propose addr reqs
      do_incorporateR a
      case outA of
        Nothing -> return ()
        (Just outA') -> responsesAt outA' .= resps)
    (Output _ _ _ _ _) -> do
      t <- get
      let (val, d) = runWriter $ propose a t
      tell d
      v <- lift $ processOutput val
      nodes . ix a . value .= Just v
      do_incorporate a

evalRequests :: (MonadRandom m, MonadTrans t, MonadState (Trace m num) (t m), Numerical num) =>
                Proposal m num -> SPAddress -> [SimulationRequest num] -> t m [Address]
evalRequests propose a srs = mapM evalRequest srs where
    evalRequest (SimulationRequest id exp env) = do
      cached <- gets $ lookupResponse a id
      case cached of
        (Just addr) -> return addr
        Nothing -> do
          addr <- eval propose exp env
          modify $ insertResponse a id addr
          return addr

-- Returns the address of the fresh node holding the result of the
-- evaluation.
-- TODO In the presence of nontrivial proposals, eval can return weights
eval :: (MonadRandom m, MonadTrans t, MonadState (Trace m num) (t m), Numerical num) =>
        Proposal m num -> Exp num -> Env -> t m Address
eval _ (Compose (Datum v)) _ = state $ addFreshNode $ Constant v
eval propose (Compose (Var n)) e = do
  let answer = case L.lookup n e of
                 Nothing -> error $ "Unbound variable " ++ show n
                 (Just a) -> Reference Nothing a
  addr <- state $ addFreshNode answer
  -- Is there a good reason why I don't care about the log density of this regenNode?
  _ <- runWriterT $ regenNode propose addr
  return addr
eval _ (Compose (Lam vs exp)) e = do
  spAddr <- state $ addFreshSP $ compoundSP vs (Compose exp) e
  state $ addFreshNode $ Constant $ Procedure spAddr
eval propose (Compose (App op args)) env = do
  op' <- eval propose (Compose op) env
  args' <- sequence $ map (flip (eval propose) env) $ map Compose $ toList args
  addr <- state $ addFreshNode (Request Nothing Nothing op' args')
  -- Is there a good reason why I don't care about the log density of this regenNode?
  _ <- runWriterT $ regenNode propose addr
  reqAddrs <- gets $ fulfilments addr
  addr' <- state $ addFreshNode (Output Nothing addr op' args' reqAddrs)
  nodes . ix addr . out_node .= Just addr'
  -- Is there a good reason why I don't care about the log density of this regenNode?
  _ <- runWriterT $ regenNode propose addr'
  return addr'

prior :: (MonadRandom m, Numerical num) => Proposal m num
prior a t =
  case t ^. nodes . hardix "Regenerating value for nonexistent node" a of
    (Output _ _ opa ps rs) -> return $ outputFor addr ps rs t where
      addr = fromJust "Regenerating value for an output with no operator" $ fromValueAt opa t

withDeterministic :: (Monad m, Numerical num) => Proposal m num -> Map Address (Value num) -> Proposal m num
withDeterministic base as a t =
    case Map.lookup a as of
      (Just v) -> writer (Left $ return v, LogDensity $ absorbVal node sp) where
        -- TODO Abstract commonality between this nonsense and absorbAt
        node = t ^. nodes . hardix "Absorbing at a nonexistent node" a
        sp = fromJust "Absorbing at a node with no operator" $ operator node t
        absorbVal (Output _ _ _ args reqs) SP{log_d_out = (Just (LogDOut f)), current = a} =
            f a args' reqs' v where
              args' = map (fromJust "absorb" . flip lookupNode t) args
              reqs' = map (fromJust "absorb" . flip lookupNode t) reqs
      Nothing  -> base a t
