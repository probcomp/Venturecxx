module Recursions where

import qualified Data.Map as M
import Data.Maybe
import Control.Monad.Trans.Writer.Strict
import Control.Monad.Trans.Class
import Control.Monad.Random -- From cabal install MonadRandom

import Language
import Trace

newtype Scaffold = Scaffold () -- TODO

scaffold_from_principal_node :: Address -> Trace rand -> Scaffold
scaffold_from_principal_node = undefined

detach :: Scaffold -> Trace rand -> Writer LogDensity (Trace rand)
detach = undefined

regen :: (MonadRandom m) => Trace m -> WriterT LogDensity m (Trace m)
regen = undefined

regenNode :: (MonadRandom m) => Trace m -> Node (SP m) -> WriterT LogDensity m (Trace m)
regenNode trace node =
    if isRegenerated node then
        return trace
    else do
        sequence_ $ map (regenNode trace) $ parents trace node
        regenValue trace node

regenValue :: (MonadRandom m) => Trace m -> Node (SP m) -> WriterT LogDensity m (Trace m)
regenValue t (Constant _) = return t
regenValue t (Reference _) = return t
-- These two clauses look an awful lot like applyPSP
regenValue t@Trace{ nodes = nodes } node@(Request _ ps) = do
  let sp@SP{ requester = req } = fromJust $ operator t node
  reqs <- lift $ req $ map (fromJust . flip M.lookup nodes) ps
  let trace' = insert t address (Request (Just reqs) ps)
  lift $ evalRequests t node reqs
          where address :: Address
                address = undefined
regenValue t@Trace{ nodes = nodes } node@(Output _ ps rs) = do
  let sp@SP{ outputter = out } = fromJust $ operator t node
  let args = map (fromJust . flip M.lookup nodes) ps
  let results = map (fromJust . flip M.lookup nodes) rs
  v <- lift $ out args results
  return $ insert t address (Output (Just v) ps rs)
          where address :: Address
                address = undefined

evalRequests :: Trace m -> Node (SP m) -> [SimulationRequest] -> m (Trace m)
evalRequests = undefined
-- eval :: Address -> Exp -> Trace -> Trace
-- eval = undefined

-- uneval :: Address -> Trace -> Trace
-- uneval = undefined
