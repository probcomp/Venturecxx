module Trace where

import qualified Data.Map as M
import Data.Maybe

import Language

newtype Address = Address Int
    deriving (Eq, Ord)

newtype SRId = SRId Int

data SimulationRequest = SimulationRequest SRId Exp Env

-- TODO An SP needing state of type a takes the a in appropriate
-- places, and offers incorporate and unincorporate functions that
-- transform states.  The Trace needs to contain a heterogeneous
-- collection of all the SP states, perhaps per
-- http://www.haskell.org/haskellwiki/Heterogenous_collections#Existential_types

-- m is presumably an instance of MonadRandom
data SP m = SP { requester :: [Node (SP m)] -> m [SimulationRequest]
               , log_d_req :: Maybe ([Node (SP m)] -> [SimulationRequest] -> Double)
               , outputter :: [Node (SP m)] -> [Node (SP m)] -> m (Value (SP m))
               , log_d_out :: Maybe ([Node (SP m)] -> [Node (SP m)] -> (Value (SP m)) -> Double)
               }

data Node proc = Constant (Value proc)
               | Reference Address
               | Request (Maybe [SimulationRequest]) [Address]
               | Output (Maybe (Value proc)) [Address] [Address]

valueOf :: Node proc -> Maybe (Value proc)
valueOf (Constant v) = Just v
valueOf (Output v _ _) = v
valueOf _ = Nothing

parentAddrs :: Node proc -> [Address]
parentAddrs (Constant _) = []
parentAddrs (Reference addr) = [addr]
parentAddrs (Request _ as) = as
parentAddrs (Output _ as as') = as ++ as'

isRegenerated :: Node proc -> Bool
isRegenerated (Constant _) = True
isRegenerated (Reference addr) = undefined -- TODO: apparently a function of the addressee
isRegenerated (Request Nothing _) = False
isRegenerated (Request (Just _) _) = True
isRegenerated (Output Nothing _ _) = False
isRegenerated (Output (Just _) _ _) = True

----------------------------------------------------------------------
-- Traces
----------------------------------------------------------------------

-- A "torus" is a trace some of whose nodes have Nothing values, and
-- some of whose Request nodes may have outstanding SimulationRequests
-- that have not yet been met.
data Trace rand = Trace (M.Map Address (Node (SP rand))) [Address] -- random choices

chaseReferences :: Trace rand -> Address -> Maybe (Node (SP rand))
chaseReferences t@(Trace m _) a = do
  n <- M.lookup a m
  chase n
    where chase (Reference a) = chaseReferences t a
          chase n = Just n

parents :: Trace rand -> Node (SP rand) -> [Node (SP rand)]
parents (Trace nodes _) node = map (fromJust . flip M.lookup nodes) $ parentAddrs node

operator :: Trace rand -> Node (SP rand) -> Maybe (SP rand)
operator t n = do a <- op_addr n
                  source <- chaseReferences t a
                  valueOf source >>= spValue
    where op_addr (Request _ (a:_)) = Just a
          op_addr (Output _ (a:_) _) = Just a
          op_addr _ = Nothing

insert :: Trace rand -> Address -> Node (SP rand) -> Trace rand
insert (Trace nodes randoms) a n = Trace (M.insert a n nodes) randoms -- TODO update random choices
