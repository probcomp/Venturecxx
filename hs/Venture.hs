module Venture where

import qualified Data.Map as M
import Data.Maybe
import Control.Monad.Random hiding (Random) -- From cabal install MonadRandom

data Value = Number Double
           | Symbol String
           | List [Value]

newtype Address = Address Int
    deriving (Eq, Ord)

newtype SimulationRequest = SimulationRequest () -- TODO

-- TODO An SP needing state of type a takes the a in appropriate
-- places, and offers incorporate and unincorporate functions that
-- transform states.  The Trace needs to contain a heterogeneous
-- collection of all the SP states, perhaps per
-- http://www.haskell.org/haskellwiki/Heterogenous_collections#Existential_types

-- m is presumably an instance of RandomMonad
data SP m = SP { requester :: [Node] -> m [SimulationRequest]
               , log_d_req :: Maybe ([Node] -> [SimulationRequest] -> Double)
               , outputter :: [Node] -> [Node] -> m Value
               , log_d_out :: Maybe ([Node] -> [Node] -> Value -> Double)
               }

data Node = Constant Value
          | Reference Address
          | Request (Maybe [SimulationRequest]) [Address]
          | Output (Maybe Value) [Address] [Address]

isRegenerated :: Node -> Bool
isRegenerated (Constant _) = True
isRegenerated (Reference addr) = undefined -- TODO
isRegenerated (Request Nothing _) = False
isRegenerated (Request (Just _) _) = True
isRegenerated (Output Nothing _ _) = False
isRegenerated (Output (Just _) _ _) = True

parentAddrs :: Node -> [Address]
parentAddrs (Constant _) = []
parentAddrs (Reference addr) = [addr]
parentAddrs (Request _ as) = as
parentAddrs (Output _ as as') = as ++ as'

parents :: Trace -> Node -> [Node]
parents (Trace nodes _) node = map (fromJust . flip M.lookup nodes) $ parentAddrs node

-- A "torus" is a trace some of whose nodes have Nothing values, and
-- some of whose Request nodes may have outstanding SimulationRequests
-- that have not yet been met.
data Trace = Trace (M.Map Address Node) [Address] -- random choices

newtype Scaffold = Scaffold () -- TODO

scaffold_from_principal_node :: Address -> Trace -> Scaffold
scaffold_from_principal_node = undefined

detach :: Scaffold -> Trace -> (Double, Trace)
detach = undefined

regen :: (MonadRandom m) => Trace -> m (Double, Trace)
regen = undefined

regenNode :: (MonadRandom m) => Node -> Trace -> m (Double, Trace)
regenNode node trace =
    if isRegenerated node then
        return (0, trace)
    else
        undefined

-- eval :: Address -> Exp -> Trace -> Trace
-- eval = undefined

-- uneval :: Address -> Trace -> Trace
-- uneval = undefined

type Kernel m a = a -> m (Double, a) -- What standard thing is this?

mix_mh_kernels :: (Monad m) => (a -> m ind) -> (a -> ind -> Double) ->
                  (ind -> Kernel m a) -> (Kernel m a)
mix_mh_kernels sampleIndex measureIndex paramK x = do
  ind <- sampleIndex x
  let ldRho = measureIndex x ind
  (alpha, x') <- paramK ind x
  let ldXi = measureIndex x' ind
  return (alpha + ldXi - ldRho, x')

metropolis_hastings :: (MonadRandom m) => Kernel m a -> a -> m a
metropolis_hastings propose x = do
  (alpha, x') <- propose x
  u <- getRandomR (0.0,1.0)
  if (log u < alpha) then
      return x'
  else
      return x



scaffold_mh_kernel :: (MonadRandom m) => Scaffold -> Kernel m Trace
scaffold_mh_kernel scaffold trace = do
  let (detachWeight, torus) = detach scaffold trace
  (regenWeight, trace') <- regen torus
  return (regenWeight - detachWeight, trace')

principal_node_mh :: (MonadRandom m) => Kernel m Trace
principal_node_mh = mix_mh_kernels sample log_density scaffold_mh_kernel where
    sample :: (MonadRandom m) => Trace -> m Scaffold
    sample trace@(Trace _ choices) = do
      index <- getRandomR (0, length choices - 1)
      return $ scaffold_from_principal_node (choices !! index) trace

    log_density :: Trace -> a -> Double
    log_density (Trace _ choices) _ = -log(fromIntegral $ length choices)
    
