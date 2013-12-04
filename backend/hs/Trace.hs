{-# LANGUAGE FlexibleContexts #-}

module Trace where

import Data.Maybe hiding (fromJust)
import qualified Data.Map as M
import qualified Data.Set as S
import Data.List (foldl)
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
data SP m = SP { requester :: SPRequester m
               , log_d_req :: Maybe ([Address] -> [SimulationRequest] -> Double)
               , outputter :: SPOutputter m
               , log_d_out :: Maybe ([Node] -> [Node] -> Value -> Double)
               }

data SPRequester m = DeterministicR ([Address] -> UniqueSource [SimulationRequest])
                   | RandomR ([Address] -> UniqueSourceT m [SimulationRequest])

data SPOutputter m = DeterministicO ([Node] -> [Node] -> Value)
                   | RandomO ([Node] -> [Node] -> m Value)

asRandomR :: (Monad m) => SPRequester m -> [Address] -> UniqueSourceT m [SimulationRequest]
asRandomR (RandomR f) as = f as
asRandomR (DeterministicR f) as = returnT $ f as

asRandomO :: (Monad m) => SPOutputter m -> [Node] -> [Node] -> m Value
asRandomO (RandomO f) args reqs = f args reqs
asRandomO (DeterministicO f) args reqs = return $ f args reqs

canAbsorb :: Node -> SP m -> Bool
canAbsorb (Request _ _ _)  SP { log_d_req = (Just _) } = True
canAbsorb (Output _ _ _ _ _) SP { log_d_out = (Just _) } = True
canAbsorb _ _ = False

absorb :: Node -> SP m -> Trace m -> Double
absorb (Request (Just reqs) _ args) SP { log_d_req = (Just f) } _ = f args reqs
absorb (Output (Just v) _ _ args reqs) SP { log_d_out = (Just f) } t = f args' reqs' v where
    args' = map (fromJust "absorb" . flip lookupNode t) args
    reqs' = map (fromJust "absorb" . flip lookupNode t) reqs
absorb _ _ _ = error "Inappropriate absorb attempt"

nullReq :: SPRequester m
nullReq = DeterministicR $ \_ -> return []

trivial_log_d_req :: a -> b -> Double
trivial_log_d_req = const $ const $ 0.0

trivialOut :: (Monad m) => SPOutputter m
trivialOut = DeterministicO self where
    self _ (n:_) = fromJust "trivialOut node had no value" $ valueOf n
    self _ _ = error "trivialOut expects at least one request result"

compoundSP :: (Monad m) => [String] -> Exp -> Env -> SP m
compoundSP formals exp env =
    SP { requester = DeterministicR req
       , log_d_req = Just $ trivial_log_d_req
       , outputter = trivialOut
       , log_d_out = Nothing
       } where
        req args = do
          freshId <- liftM SRId fresh
          let r = SimulationRequest freshId exp $ Frame (M.fromList $ zip formals args) env
          return [r]

data SPRecord m = SPRecord { sp :: (SP m)
                           , srid_seed :: UniqueSeed
                           , requests :: M.Map SRId Address
                           }

spRecord :: SP m -> SPRecord m
spRecord sp = SPRecord sp uniqueSeed M.empty

data Node = Constant Value
          | Reference (Maybe Value) Address
          | Request (Maybe [SimulationRequest]) Address [Address]
          | Output (Maybe Value) Address Address [Address] [Address]

valueOf :: Node -> Maybe Value
valueOf (Constant v) = Just v
valueOf (Reference v _) = v
valueOf (Output v _ _ _ _) = v
valueOf _ = Nothing

devalue :: Node -> Node
devalue (Constant _) = error "Cannot devalue a constant"
devalue (Reference _ a) = Reference Nothing a
devalue (Request _ a as) = Request Nothing a as
devalue (Output _ reqA opa args reqs) = Output Nothing reqA opa args reqs

parentAddrs :: Node -> [Address]
parentAddrs (Constant _) = []
parentAddrs (Reference _ addr) = [addr]
parentAddrs (Request _ a as) = a:as
parentAddrs (Output _ reqA a as as') = reqA:a:(as ++ as')

opAddr :: Node -> Maybe Address
opAddr (Request _ a _) = Just a
opAddr (Output _ _ a _ _) = Just a
opAddr _ = Nothing

requestIds :: Node -> [SRId]
requestIds (Request (Just srs) _ _) = map srid srs
    where srid (SimulationRequest id _ _) = id
requestIds _ = error "Asking for request IDs of a non-request node"

----------------------------------------------------------------------
-- Traces
----------------------------------------------------------------------

-- A "torus" is a trace some of whose nodes have Nothing values, and
-- some of whose Request nodes may have outstanding SimulationRequests
-- that have not yet been met.
data Trace rand =
    Trace { nodes :: (M.Map Address Node)
          , randoms :: S.Set Address
          , nodeChildren :: M.Map Address (S.Set Address)
          , sprs :: (M.Map SPAddress (SPRecord rand))
          , request_counts :: M.Map Address Int
          , addr_seed :: UniqueSeed
          , spaddr_seed :: UniqueSeed
          }

empty :: Trace m
empty = Trace M.empty S.empty M.empty M.empty M.empty uniqueSeed uniqueSeed

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
isRegenerated (Output Nothing _ _ _ _) = False
isRegenerated (Output (Just _) _ _ _ _) = True

operatorAddr :: Node -> Trace m -> Maybe SPAddress
operatorAddr n t = do
  a <- opAddr n
  chaseOperator a t

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

-- TODO This is only used to add values to nodes.  Enforce; maybe collapse with adjustNode?
insertNode :: Address -> Node -> Trace m -> Trace m
insertNode a n t@Trace{nodes = ns} = t{ nodes = ns'} where
    ns' = M.insert a n ns

-- TODO This is only used to remove values from nodes.  Enforce or collapse?
adjustNode :: (Node -> Node) -> Address -> Trace m -> Trace m
adjustNode f a t@Trace{nodes = ns} = t{ nodes = (M.adjust f a ns) }

deleteNode :: Address -> Trace m -> Trace m
deleteNode a t@Trace{nodes = ns, randoms = rs, nodeChildren = cs} =
    t{ nodes = ns', randoms = rs', nodeChildren = cs'' } where
        node = fromJust "Deleting a non-existent node" $ M.lookup a ns
        ns' = M.delete a ns
        rs' = S.delete a rs -- OK even if it wasn't random
        cs' = foldl foo cs $ parentAddrs node
        cs'' = M.delete a cs'
        foo cs pa = M.adjust (S.delete a) pa cs

addFreshNode :: Node -> Trace m -> (Address, Trace m)
addFreshNode node t@Trace{ nodes = ns, addr_seed = seed, randoms = rs, nodeChildren = cs } =
    (a, t{ nodes = ns', addr_seed = seed', randoms = rs', nodeChildren = cs''}) where
        (a, seed') = runUniqueSource (liftM Address fresh) seed
        ns' = M.insert a node ns
        rs' = S.insert a rs -- TODO only insert if it's actually random, duh
        cs' = foldl foo cs $ parentAddrs node
        cs'' = M.insert a S.empty cs'
        foo cs pa = M.adjust (S.insert a) pa cs

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
fulfilments a t = map (fromJust "Unfulfilled request" . flip M.lookup reqs) $ requestIds node where
    node = fromJust "Asking for fulfilments of a missing node" $ lookupNode a t
    SPRecord { requests = reqs } = fromJust "Asking for fulfilments of a node with no operator record" $ operatorRecord node t

insertResponse :: SPAddress -> SRId -> Address -> Trace m -> Trace m
insertResponse spa id a t@Trace{ sprs = ss, request_counts = r } =
    t{ sprs = M.insert spa spr' ss, request_counts = r' } where
        spr' = spr{ requests = M.insert id a reqs }
        spr@SPRecord { requests = reqs } = fromJust "Inserting response to non-SP" $ lookupSPR spa t
        r' = M.alter succ a r
        succ Nothing = Just 1
        succ (Just n) = Just (n+1)

lookupResponse :: SPAddress -> SRId -> Trace m -> Maybe Address
lookupResponse spa srid t = do
  SPRecord { requests = reqs } <- lookupSPR spa t
  M.lookup srid reqs

forgetResponses :: (SPAddress, [SRId]) -> Trace m -> Trace m
forgetResponses (spaddr, srids) t@Trace{ sprs = ss, request_counts = r } =
    t{ sprs = M.insert spaddr spr' ss, request_counts = r' } where
        spr' = spr{ requests = foldl (flip M.delete) reqs srids }
        spr@SPRecord { requests = reqs } = fromJust "Forgetting responses to non-SP" $ lookupSPR spaddr t
        r' = foldl decrement r srids
        decrement :: (M.Map Address Int) -> SRId -> (M.Map Address Int)
        decrement m srid = M.adjust (subtract 1) k m where
            k = fromJust "Forgetting response that isn't there" $ M.lookup srid reqs

runRequester :: (Monad m) => SPAddress -> [Address] -> Trace m -> m ([SimulationRequest], Trace m)
runRequester spaddr args t = do
  let spr@SPRecord { sp = SP{ requester = req }, srid_seed = seed } = fromJust "Running the requester of a non-SP" $ lookupSPR spaddr t
  (reqs, seed') <- runUniqueSourceT (asRandomR req args) seed
  let trace' = insertSPR spaddr spr{ srid_seed = seed' } t
  return (reqs, trace')

-- How many times has the given address been requested.
numRequests :: Address -> Trace m -> Int
numRequests a Trace { request_counts = r } = fromMaybe 0 $ M.lookup a r

-- Nodes in the trace that depend upon the node at the given address.
children :: Address -> Trace m -> [Address]
children a Trace{nodeChildren = cs} =
    S.toList $ fromJust "Loooking up the children of a nonexistent node" $ M.lookup a cs
