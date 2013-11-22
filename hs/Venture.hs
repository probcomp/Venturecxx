{-# LANGUAGE GeneralizedNewtypeDeriving, ExistentialQuantification #-}

module Venture where

import qualified Data.Map as M
import Data.Maybe
import Data.Monoid
import Control.Monad.Trans.Writer.Strict
import Control.Monad.Trans.Class

import Control.Monad.Random -- From cabal install MonadRandom

data Value = Number Double
           | Symbol String
           | List [Value]
           | Procedure SP

spValue :: Value -> Maybe SP
spValue (Procedure s) = Just s
spValue _ = Nothing

newtype Address = Address Int
    deriving (Eq, Ord)

newtype SimulationRequest = SimulationRequest () -- TODO

-- TODO An SP needing state of type a takes the a in appropriate
-- places, and offers incorporate and unincorporate functions that
-- transform states.  The Trace needs to contain a heterogeneous
-- collection of all the SP states, perhaps per
-- http://www.haskell.org/haskellwiki/Heterogenous_collections#Existential_types

-- m is presumably an instance of RandomMonad
data SP = forall m .
          SP { requester :: [Node] -> m [SimulationRequest]
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
isRegenerated (Reference addr) = undefined -- TODO: apparently a function of the addressee
isRegenerated (Request Nothing _) = False
isRegenerated (Request (Just _) _) = True
isRegenerated (Output Nothing _ _) = False
isRegenerated (Output (Just _) _ _) = True

chaseReferences :: Trace -> Address -> Maybe Node
chaseReferences t@(Trace m _) a = do
  n <- M.lookup a m
  chase n
    where chase :: Node -> Maybe Node
          chase (Reference a) = chaseReferences t a
          chase n = Just n

valueOf :: Node -> Maybe Value
valueOf (Constant v) = Just v
valueOf (Output v _ _) = v
valueOf _ = Nothing

parentAddrs :: Node -> [Address]
parentAddrs (Constant _) = []
parentAddrs (Reference addr) = [addr]
parentAddrs (Request _ as) = as
parentAddrs (Output _ as as') = as ++ as'

parents :: Trace -> Node -> [Node]
parents (Trace nodes _) node = map (fromJust . flip M.lookup nodes) $ parentAddrs node

operator :: Trace -> Node -> Maybe SP
operator t n = do a <- op_addr n
                  source <- chaseReferences t a
                  valueOf source >>= spValue
    where op_addr :: Node -> Maybe Address
          op_addr (Request _ (a:_)) = Just a
          op_addr (Output _ (a:_) _) = Just a
          op_addr _ = Nothing

-- A "torus" is a trace some of whose nodes have Nothing values, and
-- some of whose Request nodes may have outstanding SimulationRequests
-- that have not yet been met.
data Trace = Trace (M.Map Address Node) [Address] -- random choices

insert :: Trace -> Address -> Node -> Trace
insert (Trace nodes randoms) a n = Trace (M.insert a n nodes) randoms -- TODO update random choices

newtype Scaffold = Scaffold () -- TODO

newtype LogDensity = LogDensity Double
    deriving Random

instance Monoid LogDensity where
    mempty = LogDensity 0.0
    (LogDensity x) `mappend` (LogDensity y) = LogDensity $ x + y

log_density_nedate :: LogDensity -> LogDensity
log_density_nedate (LogDensity x) = LogDensity $ -x

scaffold_from_principal_node :: Address -> Trace -> Scaffold
scaffold_from_principal_node = undefined

detach :: Scaffold -> Trace -> Writer LogDensity Trace
detach = undefined

regen :: (MonadRandom m) => Trace -> WriterT LogDensity m Trace
regen = undefined

regenNode :: (MonadRandom m) => Trace -> Node -> WriterT LogDensity m Trace
regenNode trace node =
    if isRegenerated node then
        return trace
    else do
        sequence_ $ map (regenNode trace) $ parents trace node
        regenValue trace node

regenValue :: (MonadRandom m) => Trace -> Node -> WriterT LogDensity m Trace
regenValue t (Constant _) = return t
regenValue t (Reference _) = return t
-- regenValue t@(Trace nodes _) node@(Request _ ps) = do
--   let sp@SP{ requester = req } = fromJust $ operator t node
--   reqs <- lift $ req $ map (fromJust . flip M.lookup nodes) ps
--   let trace' = insert t address (Request reqs ps)
--   lift $ evalRequests t node reqs
--           where address :: Address
--                 address = undefined

evalRequests :: Trace -> Node -> [SimulationRequest] -> m Trace
evalRequests = undefined
-- eval :: Address -> Exp -> Trace -> Trace
-- eval = undefined

-- uneval :: Address -> Trace -> Trace
-- uneval = undefined

type Kernel m a = a -> WriterT LogDensity m a

mix_mh_kernels :: (Monad m) => (a -> m ind) -> (a -> ind -> LogDensity) ->
                  (ind -> Kernel m a) -> (Kernel m a)
mix_mh_kernels sampleIndex measureIndex paramK x = do
  ind <- lift $ sampleIndex x
  let ldRho = measureIndex x ind
  tell ldRho
  x' <- paramK ind x
  let ldXi = measureIndex x' ind
  tell $ log_density_nedate ldXi
  return x'

metropolis_hastings :: (MonadRandom m) => Kernel m a -> a -> m a
metropolis_hastings propose x = do
  (x', (LogDensity alpha)) <- runWriterT $ propose x
  u <- getRandomR (0.0,1.0)
  if (log u < alpha) then
      return x'
  else
      return x



scaffold_mh_kernel :: (MonadRandom m) => Scaffold -> Kernel m Trace
scaffold_mh_kernel scaffold trace = do
  torus <- censor log_density_nedate $ stupid $ detach scaffold trace
  regen torus
        where stupid :: (Monad m) => Writer w a -> WriterT w m a
              stupid = WriterT . return . runWriter

principal_node_mh :: (MonadRandom m) => Kernel m Trace
principal_node_mh = mix_mh_kernels sample log_density scaffold_mh_kernel where
    sample :: (MonadRandom m) => Trace -> m Scaffold
    sample trace@(Trace _ choices) = do
      index <- getRandomR (0, length choices - 1)
      return $ scaffold_from_principal_node (choices !! index) trace

    log_density :: Trace -> a -> LogDensity
    log_density (Trace _ choices) _ = LogDensity $ -log(fromIntegral $ length choices)
    
