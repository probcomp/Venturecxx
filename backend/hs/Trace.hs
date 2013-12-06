{-# LANGUAGE FlexibleContexts, TemplateHaskell #-}

module Trace where

import Debug.Trace
import Data.Maybe hiding (fromJust)
import qualified Data.Map as M
import qualified Data.Set as S
import Data.List (foldl)
import Control.Lens  -- from cabal install lens
import Control.Monad.State hiding (state) -- :set -hide-package monads-tf-0.1.0.1
import Control.Monad.Writer.Class

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
    deriving (Eq, Ord, Show)

newtype SPAddress = SPAddress Unique
    deriving (Eq, Ord, Show)

newtype SRId = SRId Unique
    deriving (Eq, Ord, Show)

data SimulationRequest = SimulationRequest SRId Exp Env
    deriving Show

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

instance Show (SP m) where
    show _ = "A stochastic procedure"

-- TODO Is there a nice way to unify these two data types and their
-- methods?
data SPRequester m = DeterministicR ([Address] -> UniqueSource [SimulationRequest])
                   | RandomR ([Address] -> UniqueSourceT m [SimulationRequest])

data SPOutputter m = DeterministicO ([Node] -> [Node] -> Value)
                   | RandomO ([Node] -> [Node] -> m Value)

asRandomR :: (Monad m) => SPRequester m -> [Address] -> UniqueSourceT m [SimulationRequest]
asRandomR (RandomR f) as = f as
asRandomR (DeterministicR f) as = returnT $ f as

isRandomR :: SPRequester m -> Bool
isRandomR (RandomR _) = True
isRandomR (DeterministicR _) = False

asRandomO :: (Monad m) => SPOutputter m -> [Node] -> [Node] -> m Value
asRandomO (RandomO f) args reqs = f args reqs
asRandomO (DeterministicO f) args reqs = return $ f args reqs

isRandomO :: SPOutputter m -> Bool
isRandomO (RandomO _) = True
isRandomO (DeterministicO _) = False

canAbsorb :: Node -> SP m -> Bool
canAbsorb (Request _ _ _ _)  SP { log_d_req = (Just _) } = True
canAbsorb (Output _ _ _ _ _) SP { log_d_out = (Just _) } = True
canAbsorb _ _ = False

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
       , log_d_out = Nothing -- Or Just (0 if it's right, -inf if not?)
       } where
        req args = do
          freshId <- liftM SRId fresh
          let r = SimulationRequest freshId exp $ Frame (M.fromList $ zip formals args) env
          return [r]

data SPRecord m = SPRecord { sp :: (SP m)
                           , srid_seed :: UniqueSeed
                           , requests :: M.Map SRId Address
                           }
    deriving Show

spRecord :: SP m -> SPRecord m
spRecord sp = SPRecord sp uniqueSeed M.empty

data Node = Constant Value
          | Reference (Maybe Value) Address
          | Request (Maybe [SimulationRequest]) (Maybe Address) Address [Address]
          | Output (Maybe Value) Address Address [Address] [Address]
    deriving Show

valueOf :: Node -> Maybe Value
valueOf (Constant v) = Just v
valueOf (Reference v _) = v
valueOf (Output v _ _ _ _) = v
valueOf _ = Nothing

revalue :: Node -> Maybe Value -> Node
revalue (Constant _) _ = error "Cannot revalue a constant"
revalue (Reference _ a) v = Reference v a
-- This is a slight violation of the lens laws
revalue (Request _ outA a as) Nothing = Request Nothing outA a as
revalue r@(Request _ _ _ _) _ = r
revalue (Output _ reqA opa args reqs) v = Output v reqA opa args reqs

value :: Simple Lens Node (Maybe Value)
value = lens valueOf revalue

sim_reqs :: Simple Lens Node (Maybe [SimulationRequest])
sim_reqs = lens _requests re_requests where
    _requests (Request r _ _ _) = r
    _requests _ = Nothing
    re_requests (Request _ outA a args) r = (Request r outA a args)
    re_requests n Nothing = n
    re_requests n _ = error "Trying to set requests for a non-request node."

parentAddrs :: Node -> [Address]
parentAddrs (Constant _) = []
parentAddrs (Reference _ addr) = [addr]
parentAddrs (Request _ _ a as) = a:as
parentAddrs (Output _ reqA a as as') = reqA:a:(as ++ as')

opAddr :: Node -> Maybe Address
opAddr (Request _ _ a _) = Just a
opAddr (Output _ _ a _ _) = Just a
opAddr _ = Nothing

requestIds :: Node -> [SRId]
requestIds (Request (Just srs) _ _ _) = map srid srs
    where srid (SimulationRequest id _ _) = id
requestIds _ = error "Asking for request IDs of a non-request node"

addOutput :: Address -> Node -> Node
addOutput outA (Request v _ a as) = Request v (Just outA) a as
addOutput _ n = n

out_node :: Simple Setter Node (Maybe Address)
out_node = sets _out_node where
    _out_node f (Request v outA a as) = Request v (f outA) a as
    _out_node _ _ = error "Non-Request nodes do not have corresponding output nodes"

responses :: Simple Lens Node [Address]
responses = lens _responses addResponses where
    _responses (Output _ _ _ _ rs) = rs
    addResponses (Output v reqA a as _) resps = Output v reqA a as resps
    addResponses n _ = n

----------------------------------------------------------------------
-- Traces
----------------------------------------------------------------------

-- A "torus" is a trace some of whose nodes have Nothing values, and
-- some of whose Request nodes may have outstanding SimulationRequests
-- that have not yet been met.
data Trace rand =
    Trace { _nodes :: (M.Map Address Node)
          , _randoms :: S.Set Address
          , _nodeChildren :: M.Map Address (S.Set Address)
          , _sprs :: (M.Map SPAddress (SPRecord rand))
          , _request_counts :: M.Map Address Int
          , _addr_seed :: UniqueSeed
          , _spaddr_seed :: UniqueSeed
          }
    deriving Show

-- This needs to be late in the file because of circular type
-- dependencies?
makeLenses ''Trace

empty :: Trace m
empty = Trace M.empty S.empty M.empty M.empty M.empty uniqueSeed uniqueSeed

chaseReferences :: Address -> Trace m -> Maybe Node
chaseReferences a t = do
  n <- t^.nodes.(at a)
  chase n
    where chase (Reference _ a) = chaseReferences a t
          chase n = Just n

isRegenerated :: Node -> Bool
isRegenerated (Constant _) = True
isRegenerated (Reference Nothing _) = False
isRegenerated (Reference (Just _) _) = True
isRegenerated (Request Nothing _ _ _) = False
isRegenerated (Request (Just _) _ _ _) = True
isRegenerated (Output Nothing _ _ _ _) = False
isRegenerated (Output (Just _) _ _ _ _) = True

operatorAddr :: Node -> Trace m -> Maybe SPAddress
operatorAddr n t = do
  a <- opAddr n
  chaseOperator a t

chaseOperator :: Address -> Trace m -> Maybe SPAddress
chaseOperator a t = do
  -- TODO This chase may be superfluous now that Reference nodes hold
  -- their values.
  source <- chaseReferences a t
  valueOf source >>= spValue

operatorRecord :: Node -> Trace m -> Maybe (SPRecord m)
operatorRecord n t = operatorAddr n t >>= (\addr -> t ^. sprs . at addr)

operator :: Node -> Trace m -> Maybe (SP m)
operator n = liftM sp . operatorRecord n

isRandomNode :: Node -> Trace m -> Bool
isRandomNode n@(Request _ _ _ _) t = case operator n t of
                                       Nothing -> False
                                       (Just sp) -> isRandomR $ requester sp
isRandomNode n@(Output _ _ _ _ _) t = case operator n t of
                                        Nothing -> False
                                        (Just sp) -> isRandomO $ outputter sp
isRandomNode _ _ = False

-- TODO Can I turn these three into an appropriate lens?
lookupNode :: Address -> Trace m -> Maybe Node
lookupNode a t = t ^. nodes . at a

deleteNode :: Address -> Trace m -> Trace m
deleteNode a t@Trace{_nodes = ns, _randoms = rs, _nodeChildren = cs} =
    t{ _nodes = ns', _randoms = rs', _nodeChildren = cs'' } where
        node = fromJust "Deleting a non-existent node" $ M.lookup a ns
        ns' = M.delete a ns
        rs' = S.delete a rs -- OK even if it wasn't random
        cs' = foldl foo cs $ parentAddrs node
        cs'' = M.delete a cs'
        foo cs pa = M.adjust (S.delete a) pa cs

addFreshNode :: Node -> Trace m -> (Address, Trace m)
addFreshNode node t@Trace{ _nodes = ns, _addr_seed = seed, _randoms = rs, _nodeChildren = cs } =
    (a, t{ _nodes = ns', _addr_seed = seed', _randoms = rs', _nodeChildren = cs''}) where
        (a, seed') = runUniqueSource (liftM Address fresh) seed
        ns' = M.insert a node ns
        -- TODO Argh! Need to maintain the randomness of nodes under
        -- inference-caused updates to the SPs that are their
        -- operators.
        rs' = if isRandomNode node t then
                  S.insert a rs
              else
                  rs
        cs' = foldl foo cs $ parentAddrs node
        cs'' = M.insert a S.empty cs'
        foo cs pa = M.adjust (S.insert a) pa cs

lookupSPR :: SPAddress -> Trace m -> Maybe (SPRecord m)
lookupSPR spa t = t ^. sprs . at spa

insertSPR :: SPAddress -> (SPRecord m) -> Trace m -> Trace m
insertSPR addr spr t = t & sprs . at addr .~ Just spr

addFreshSP :: SP m -> Trace m -> (SPAddress, Trace m)
addFreshSP sp t@Trace{ _sprs = ss, _spaddr_seed = seed } = (a, t{ _sprs = ss', _spaddr_seed = seed'}) where
    (a, seed') = runUniqueSource (liftM SPAddress fresh) seed
    ss' = M.insert a (spRecord sp) ss

fulfilments :: Address -> Trace m -> [Address]
-- The addresses of the responses to the requests made by the Request
-- node at Address.
fulfilments a t = map (fromJust "Unfulfilled request" . flip M.lookup reqs) $ requestIds node where
    node = fromJust "Asking for fulfilments of a missing node" $ lookupNode a t
    SPRecord { requests = reqs } = fromJust "Asking for fulfilments of a node with no operator record" $ operatorRecord node t

insertResponse :: SPAddress -> SRId -> Address -> Trace m -> Trace m
insertResponse spa id a t@Trace{ _sprs = ss, _request_counts = r } =
    t{ _sprs = M.insert spa spr' ss, _request_counts = r' } where
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
forgetResponses (spaddr, srids) t@Trace{ _sprs = ss, _request_counts = r } =
    t{ _sprs = M.insert spaddr spr' ss, _request_counts = r' } where
        spr' = spr{ requests = foldl (flip M.delete) reqs srids }
        spr@SPRecord { requests = reqs } = fromJust "Forgetting responses to non-SP" $ lookupSPR spaddr t
        r' = foldl decrement r srids
        decrement :: (M.Map Address Int) -> SRId -> (M.Map Address Int)
        decrement m srid = M.update maybePred k m where
            k = fromJust "Forgetting response that isn't there" $ M.lookup srid reqs
            maybePred 1 = Nothing
            maybePred n = Just $ n-1

runRequester :: (Monad m) => SPAddress -> [Address] -> Trace m -> m ([SimulationRequest], Trace m)
runRequester spaddr args t = do
  let spr@SPRecord { sp = SP{ requester = req }, srid_seed = seed } = fromJust "Running the requester of a non-SP" $ lookupSPR spaddr t
  (reqs, seed') <- runUniqueSourceT (asRandomR req args) seed
  let trace' = insertSPR spaddr spr{ srid_seed = seed' } t
  return (reqs, trace')

-- How many times has the given address been requested.
numRequests :: Address -> Trace m -> Int
numRequests a t = fromMaybe 0 $ t^.request_counts.at a

-- Nodes in the trace that depend upon the node at the given address.
children :: Address -> Trace m -> [Address]
children a t = t ^. nodeChildren . at a & fromJust "Loooking up the children of a nonexistent node" & S.toList

-- TODO Use of Template Haskell seems to force this to be in the same
-- block of code as lookupNode.
absorb :: Node -> SP m -> Trace m -> Double
absorb (Request (Just reqs) _ _ args) SP { log_d_req = (Just f) } _ = f args reqs
absorb (Output (Just v) _ _ args reqs) SP { log_d_out = (Just f) } t = f args' reqs' v where
    args' = map (fromJust "absorb" . flip lookupNode t) args
    reqs' = map (fromJust "absorb" . flip lookupNode t) reqs
absorb _ _ _ = error "Inappropriate absorb attempt"

absorbAt :: (MonadState (Trace m1) m, MonadWriter LogDensity m) => Address -> m ()
absorbAt a = do
  node <- use $ nodes . hardix "Absorbing at a nonexistent node" a
  sp <- gets $ fromJust "Absorbing at a node with no operator" . operator node
  wt <- gets $ absorb node sp
  tell $ LogDensity wt

----------------------------------------------------------------------
-- Invariants that traces ought to obey

referencedInvalidAddresses :: Trace m -> [Address]
referencedInvalidAddresses t = invalidParentAddresses t
                               ++ invalidRandomChoices t
                               ++ invalidNodeChildrenKeys t
                               ++ invalidNodeChildren t
                               ++ invalidRequestedAddresses t
                               ++ invalidRequestCountKeys t

invalidParentAddresses t = filter (invalidAddress t) $ concat $ map parentAddrs $ M.elems $ t ^. nodes
invalidRandomChoices t = filter (invalidAddress t) $ S.toList $ t ^. randoms
invalidNodeChildrenKeys t = filter (invalidAddress t) $ M.keys $ t ^. nodeChildren
invalidNodeChildren t = filter (invalidAddress t) $ concat $ map S.toList $ M.elems $ t ^. nodeChildren
invalidRequestedAddresses t = filter (invalidAddress t) $ concat $ map (M.elems . requests) $ M.elems $ t ^. sprs
invalidRequestCountKeys t = filter (invalidAddress t) $ M.keys $ t ^. request_counts

invalidAddress :: Trace m -> Address -> Bool
invalidAddress t a = not $ isJust $ lookupNode a t

traceShowTrace :: (Trace m) -> a -> a
traceShowTrace t = traceShow (referencedInvalidAddresses t) . traceShow t
