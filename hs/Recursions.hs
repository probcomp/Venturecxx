module Recursions where

import qualified Data.Map as M
import Data.Maybe
import Control.Monad
import Control.Monad.Trans.Writer.Strict
import Control.Monad.Trans.Class
import Control.Monad.Random -- From cabal install MonadRandom
import Prelude hiding (lookup)

import Language hiding (Value, Exp, Env, lookup)
import qualified Language as L
import Trace

newtype Scaffold = Scaffold () -- TODO

scaffold_from_principal_node :: Address -> Trace rand -> Scaffold
scaffold_from_principal_node = undefined

detach :: Scaffold -> Trace rand -> Writer LogDensity (Trace rand)
detach = undefined

regen :: (MonadRandom m) => Trace m -> WriterT LogDensity m (Trace m)
regen = undefined

regenNode :: (MonadRandom m) => Trace m -> Address -> WriterT LogDensity m (Trace m)
regenNode trace a = go $ fromJust $ lookup trace a
    where go node = if isRegenerated node then
                        return trace
                    else do
                      sequence_ $ map (regenNode trace) $ parentAddrs node
                      regenValue trace a

regenValue :: (MonadRandom m) => Trace m -> Address -> WriterT LogDensity m (Trace m)
regenValue t@Trace{ nodes = nodes } a = go $ fromJust $ lookup t a where
    go (Constant _) = return t
    go (Reference _) = return t
    -- These two clauses look an awful lot like applyPSP
    go node@(Request _ ps) = do
       let sp@SP{ requester = req } = fromJust $ operator t node
       reqs <- lift $ req ps
       let trace' = insert t a (Request (Just reqs) ps)
       lift $ evalRequests t (fromJust $ operatorAddr t node) reqs
    go node@(Output _ ps rs) = do
       let sp@SP{ outputter = out } = fromJust $ operator t node
       let args = map (fromJust . flip M.lookup nodes) ps
       let results = map (fromJust . flip M.lookup nodes) rs
       v <- lift $ out args results
       return $ insert t a (Output (Just v) ps rs)

evalRequests :: (Monad m) => Trace m -> SPAddress -> [SimulationRequest] -> m (Trace m)
evalRequests t a srs = foldM evalRequest t srs where
    -- evalRequest :: Trace m -> SimulationRequest -> m (Trace m) but it's the same m
    evalRequest t (SimulationRequest id exp env) =
        if (cached t a id) then
            return t
        else do
          (t', addr) <- eval exp env t
          return $ cache t a id addr
    cached :: Trace m -> SPAddress -> SRId -> Bool
    cached = undefined
    cache :: Trace m -> SPAddress -> SRId -> Address -> Trace m
    cache = undefined

-- Returns the updated trace and the address of the new node for the
-- result of the evaluation.
eval :: (Monad m) => Exp -> Env -> Trace m -> m ((Trace m), Address)
eval (Datum v) _ t = return $ addFreshNode t answer where
    answer = Constant v
eval (Variable n) e t = return $ addFreshNode t answer where
    answer = case L.lookup n e of
               Nothing -> error $ "Unbound variable " ++ show n
               (Just a) -> Reference a
eval (Lam vs exp) e t = return $ addFreshNode t' answer where
    (t',spaddr) = addFreshSP t sp
    sp = compoundSP vs exp e
    answer = Constant $ Procedure spaddr

-- uneval :: Address -> Trace -> Trace
-- uneval = undefined
