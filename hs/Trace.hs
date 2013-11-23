module Trace where

import qualified Data.Map as M
import Data.Maybe

import Language hiding (Value, Exp, Env)
import qualified Language as L

type Value = L.Value SPAddress
type Exp = L.Exp Value
type Env = L.Env String Address

newtype Address = Address Int
    deriving (Eq, Ord)

newtype SPAddress = SPAddress Int
    deriving (Eq, Ord)

newtype SRId = SRId Int

data SimulationRequest = SimulationRequest SRId Exp Env

-- TODO An SP needing state of type a takes the a in appropriate
-- places, and offers incorporate and unincorporate functions that
-- transform states.  The Trace needs to contain a heterogeneous
-- collection of all the SP states, perhaps per
-- http://www.haskell.org/haskellwiki/Heterogenous_collections#Existential_types

-- m is presumably an instance of MonadRandom
data SP m = SP { requester :: [Address] -> m [SimulationRequest]
               , log_d_req :: Maybe ([Address] -> [SimulationRequest] -> Double)
               , outputter :: [Node] -> [Node] -> m Value
               , log_d_out :: Maybe ([Node] -> [Node] -> Value -> Double)
               }

nullReq :: (Monad m) => a -> m [SimulationRequest]
nullReq _ = return []

trivial_log_d_req :: a -> b -> Double
trivial_log_d_req = const $ const $ 0.0

trivialOut :: [Node] -> [Node] -> m Value
trivialOut = undefined

compoundSP :: (Monad m) => [String] -> Exp -> Env -> SP m
compoundSP formals exp env =
    SP { requester = req
       , log_d_req = Just $ trivial_log_d_req
       , outputter = trivialOut
       , log_d_out = Nothing
       } where
        req args = return [r] where
            r :: SimulationRequest
            r = undefined
--            r = SimulationRequest undefined exp $ Frame (M.fromList $ zip formals args) env

data Node = Constant Value
          | Reference Address
          | Request (Maybe [SimulationRequest]) [Address]
          | Output (Maybe Value) [Address] [Address]

valueOf :: Node -> Maybe Value
valueOf (Constant v) = Just v
valueOf (Output v _ _) = v
valueOf _ = Nothing

parentAddrs :: Node -> [Address]
parentAddrs (Constant _) = []
parentAddrs (Reference addr) = [addr]
parentAddrs (Request _ as) = as
parentAddrs (Output _ as as') = as ++ as'

isRegenerated :: Node -> Bool
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
data Trace rand = 
    Trace { nodes :: (M.Map Address Node)
          , randoms :: [Address]
          , sps :: (M.Map SPAddress (SP rand))
          }

chaseReferences :: Trace rand -> Address -> Maybe Node
chaseReferences t@Trace{ nodes = m } a = do
  n <- M.lookup a m
  chase n
    where chase (Reference a) = chaseReferences t a
          chase n = Just n

parents :: Trace rand -> Node -> [Node]
parents Trace{ nodes = n } node = map (fromJust . flip M.lookup n) $ parentAddrs node

operatorAddr :: Trace rand -> Node -> Maybe SPAddress
operatorAddr t@Trace{ sps = ss } n = do
  a <- op_addr n
  source <- chaseReferences t a
  valueOf source >>= spValue
    where op_addr (Request _ (a:_)) = Just a
          op_addr (Output _ (a:_) _) = Just a
          op_addr _ = Nothing

operator :: Trace rand -> Node -> Maybe (SP rand)
operator t@Trace{ sps = ss } n = operatorAddr t n >>= (flip M.lookup ss)

lookup :: Trace rand -> Address -> Maybe Node
lookup Trace{ nodes = m } a = M.lookup a m

insert :: Trace rand -> Address -> Node -> Trace rand
insert t@Trace{nodes = ns} a n = t{ nodes = (M.insert a n ns) } -- TODO update random choices

addFreshNode :: Trace m -> Node -> (Trace m, Address)
addFreshNode = undefined

addFreshSP :: Trace m -> SP m -> (Trace m, SPAddress)
addFreshSP = undefined
