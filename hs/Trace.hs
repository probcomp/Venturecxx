{-# LANGUAGE FlexibleContexts #-}

module Trace where

import qualified Data.Map as M
import Control.Monad.State hiding (state)

import Utils
import Language hiding (Value, Exp, Env)
import qualified Language as L

-- TODO The version of state that comes from Control.Monad.State on
-- moria appears to have too restrictive a type.
state :: MonadState s m => (s -> (a, s)) -> m a
state action = do
  s <- get
  let (a, s') = action s
  put s'
  return a

type Value = L.Value SPAddress
type Exp = L.Exp Value
type Env = L.Env String Address

newtype Address = Address Unique
    deriving (Eq, Ord)

newtype SPAddress = SPAddress Unique
    deriving (Eq, Ord, Show)

newtype SRId = SRId Unique
    deriving (Eq, Ord)

data SimulationRequest = SimulationRequest SRId Exp Env

-- TODO An SP needing state of type a takes the a in appropriate
-- places, and offers incorporate and unincorporate functions that
-- transform states.  The Trace needs to contain a heterogeneous
-- collection of all the SP states, perhaps per
-- http://www.haskell.org/haskellwiki/Heterogenous_collections#Existential_types

-- m is presumably an instance of MonadRandom
data SP m = SP { requester :: [Address] -> UniqueSourceT m [SimulationRequest]
               , log_d_req :: Maybe ([Address] -> [SimulationRequest] -> Double)
               , outputter :: [Node] -> [Node] -> m Value
               , log_d_out :: Maybe ([Node] -> [Node] -> Value -> Double)
               }

data SPRecord m = SPRecord { sp :: (SP m)
                           , srid_seed :: UniqueSeed
                           , requests :: M.Map SRId Address
                           }

spRecord :: SP m -> SPRecord m
spRecord sp = SPRecord sp uniqueSeed M.empty

nullReq :: (Monad m) => a -> m [SimulationRequest]
nullReq _ = return []

trivial_log_d_req :: a -> b -> Double
trivial_log_d_req = const $ const $ 0.0

trivialOut :: (Monad m) => a -> [Node] -> m Value
trivialOut _ (n:_) = return $ fromJust "trivialOut node had no value" $ valueOf n
trivialOut _ _ = error "trivialOut expects at least one request result"

compoundSP :: (Monad m) => [String] -> Exp -> Env -> SP m
compoundSP formals exp env =
    SP { requester = req
       , log_d_req = Just $ trivial_log_d_req
       , outputter = trivialOut
       , log_d_out = Nothing
       } where
        req args = do
          freshId <- liftM SRId fresh
          let r = SimulationRequest freshId exp $ Frame (M.fromList $ zip formals args) env
          return [r]

data Node = Constant Value
          | Reference (Maybe Value) Address
          | Request (Maybe [SimulationRequest]) Address [Address]
          | Output (Maybe Value) Address [Address] [Address]

valueOf :: Node -> Maybe Value
valueOf (Constant v) = Just v
valueOf (Reference v _) = v
valueOf (Output v _ _ _) = v
valueOf _ = Nothing

parentAddrs :: Node -> [Address]
parentAddrs (Constant _) = []
parentAddrs (Reference _ addr) = [addr]
parentAddrs (Request _ a as) = a:as
parentAddrs (Output _ a as as') = a:(as ++ as')

----------------------------------------------------------------------
-- Traces
----------------------------------------------------------------------

-- A "torus" is a trace some of whose nodes have Nothing values, and
-- some of whose Request nodes may have outstanding SimulationRequests
-- that have not yet been met.
data Trace rand =
    Trace { nodes :: (M.Map Address Node)
          , randoms :: [Address]
          , sprs :: (M.Map SPAddress (SPRecord rand))
          , addr_seed :: UniqueSeed
          , spaddr_seed :: UniqueSeed
          }

empty :: Trace m
empty = Trace M.empty [] M.empty uniqueSeed uniqueSeed

chaseReferences :: Address -> Trace m -> Maybe Node
chaseReferences a t@Trace{ nodes = m } = do
  n <- M.lookup a m
  chase n
    where chase (Reference _ a) = chaseReferences a t
          chase n = Just n

isRegenerated :: Node -> Bool
isRegenerated (Constant _) = True
isRegenerated (Reference Nothing _) = False
isRegenerated (Reference (Just _) _) = True
isRegenerated (Request Nothing _ _) = False
isRegenerated (Request (Just _) _ _) = True
isRegenerated (Output Nothing _ _ _) = False
isRegenerated (Output (Just _) _ _ _) = True

operatorAddr :: Node -> Trace m -> Maybe SPAddress
operatorAddr n t = do
  a <- op_addr n
  chaseOperator a t
    where op_addr (Request _ a _) = Just a
          op_addr (Output _ a _ _) = Just a
          op_addr _ = Nothing

chaseOperator :: Address -> Trace m -> Maybe SPAddress
chaseOperator a t = do
  -- TODO This chase may be superfluous now that Reference nodes hold
  -- their values, which would mean operatorAddr doesn't need the
  -- Trace either.
  source <- chaseReferences a t
  valueOf source >>= spValue

operatorRecord :: Node -> Trace m -> Maybe (SPRecord m)
operatorRecord n t@Trace{ sprs = ss } = operatorAddr n t >>= (flip M.lookup ss)

operator :: Node -> Trace m -> Maybe (SP m)
operator n t@Trace{ sprs = ss } = operatorAddr n t >>= (liftM sp . flip M.lookup ss)

lookupNode :: Address -> Trace m -> Maybe Node
lookupNode a Trace{ nodes = m } = M.lookup a m

insertNode :: Address -> Node -> Trace m -> Trace m
insertNode a n t@Trace{nodes = ns} = t{ nodes = (M.insert a n ns) } -- TODO update random choices

addFreshNode :: Node -> Trace m -> (Address, Trace m)
addFreshNode node t@Trace{ nodes = ns, addr_seed = seed } = (a, t{ nodes = ns', addr_seed = seed'}) where
    (a, seed') = runUniqueSource (liftM Address fresh) seed
    ns' = M.insert a node ns

lookupSPR :: SPAddress -> Trace m -> Maybe (SPRecord m)
lookupSPR spa Trace{ sprs = m } = M.lookup spa m

insertSPR :: SPAddress -> (SPRecord m) -> Trace m -> Trace m
insertSPR addr spr t@Trace{ sprs = ss } = t{ sprs = M.insert addr spr ss }

addFreshSP :: SP m -> Trace m -> (SPAddress, Trace m)
addFreshSP sp t@Trace{ sprs = ss, spaddr_seed = seed } = (a, t{ sprs = ss', spaddr_seed = seed'}) where
    (a, seed') = runUniqueSource (liftM SPAddress fresh) seed
    ss' = M.insert a (spRecord sp) ss

fulfilments :: Address -> Trace m -> [Address]
-- The addresses of the responses to the requests made by the Request
-- node at Address.
fulfilments a t = map (fromJust "Unfulfilled request" . flip M.lookup reqs) $ srids node where
    node = fromJust "Asking for fulfilments of a missing node" $ lookupNode a t
    SPRecord { requests = reqs } = fromJust "Asking for fulfilments of a node with no operator record" $ operatorRecord node t
    srids (Request (Just srs) _ _) = map srid srs
    srids _ = error "Asking for fulfilments of a non-request node"
    srid (SimulationRequest id _ _) = id

insertResponse :: SPAddress -> SRId -> Address -> Trace m -> Trace m
insertResponse spa id a t@Trace{ sprs = ss } = t{ sprs = M.insert spa spr' ss } where
    spr' = spr{ requests = M.insert id a reqs }
    spr@SPRecord { requests = reqs } = fromJust "Inserting response to non-SP" $ lookupSPR spa t

lookupResponse :: SPAddress -> SRId -> Trace m -> Maybe Address
lookupResponse spa srid t = do
  SPRecord { requests = reqs } <- lookupSPR spa t
  M.lookup srid reqs

runRequester :: (Monad m) => SPAddress -> [Address] -> Trace m -> m ([SimulationRequest], Trace m)
runRequester spaddr args t = do
  let spr@SPRecord { sp = SP{ requester = req }, srid_seed = seed } = fromJust "Running the requester of a non-SP" $ lookupSPR spaddr t
  (reqs, seed') <- runUniqueSourceT (req args) seed
  let trace' = insertSPR spaddr spr{ srid_seed = seed' } t
  return (reqs, trace')

-- How many times has the given address been requested by the SP at
-- the given address.  Presumably, only one SP ever requests any given
-- address, because their caches are independent.
numRequests :: Address -> SPAddress -> Trace m -> Int
numRequests = undefined

-- Nodes in the trace that depend upon the node at the given address.
children :: Address -> Trace m -> [Address]
children = undefined
