{-# LANGUAGE FlexibleContexts #-}

module Trace where

import qualified Data.Map as M
import Data.Maybe
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

newtype SPAddress = SPAddress Int
    deriving (Eq, Ord)

newtype SRId = SRId Unique
    deriving (Eq, Ord)

data SimulationRequest = SimulationRequest SRId Exp Env

-- TODO An SP needing state of type a takes the a in appropriate
-- places, and offers incorporate and unincorporate functions that
-- transform states.  The Trace needs to contain a heterogeneous
-- collection of all the SP states, perhaps per
-- http://www.haskell.org/haskellwiki/Heterogenous_collections#Existential_types

-- m is presumably an instance of MonadRandom
-- TODO This type signature makes it unclear whether the relevant
-- lists include the operator itself, or just the arguments.
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
trivialOut _ (n:_) = return $ fromJust $ valueOf n -- TODO Probably wrong if n is a Reference node, e.g., (lambda (x) x)
trivialOut _ _ = error "trivialOut expects at least one request result"

compoundSP :: (Monad m) => [String] -> Exp -> Env -> SP m
compoundSP formals exp env =
    SP { requester = req
       , log_d_req = Just $ trivial_log_d_req
       , outputter = trivialOut
       , log_d_out = Nothing
       } where
        -- TODO This requester assumes the operator node is stripped out of the arguments
        req args = do
          freshId <- liftM SRId fresh
          let r = SimulationRequest freshId exp $ Frame (M.fromList $ zip formals args) env
          return [r]

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
          }

chaseReferences :: Address -> Trace m -> Maybe Node
chaseReferences a t@Trace{ nodes = m } = do
  n <- M.lookup a m
  chase n
    where chase (Reference a) = chaseReferences a t
          chase n = Just n

isRegenerated :: Node -> Trace m -> Bool
isRegenerated (Constant _) _ = True
isRegenerated (Reference addr) t = isRegenerated (fromJust $ chaseReferences addr t) t
isRegenerated (Request Nothing _) _ = False
isRegenerated (Request (Just _) _) _ = True
isRegenerated (Output Nothing _ _) _ = False
isRegenerated (Output (Just _) _ _) _ = True

operatorAddr :: Node -> Trace m -> Maybe SPAddress
operatorAddr n t@Trace{ sprs = ss } = do
  a <- op_addr n
  source <- chaseReferences a t
  valueOf source >>= spValue
    where op_addr (Request _ (a:_)) = Just a
          op_addr (Output _ (a:_) _) = Just a
          op_addr _ = Nothing

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
addFreshSP = undefined

fulfilments :: Address -> Trace m -> [Address]
-- The addresses of the responses to the requests made by the Request
-- node at Address.
fulfilments = undefined

insertResponse :: SPAddress -> SRId -> Address -> Trace m -> Trace m
insertResponse spa id a t@Trace{ sprs = ss } = t{ sprs = M.insert spa spr' ss } where
    spr' = spr{ requests = M.insert id a reqs }
    spr@SPRecord { requests = reqs } = fromJust $ lookupSPR spa t

lookupResponse :: SPAddress -> SRId -> Trace m -> Maybe Address
lookupResponse spa srid t = do
  SPRecord { requests = reqs } <- lookupSPR spa t
  M.lookup srid reqs

runRequester :: (Monad m) => SPAddress -> [Address] -> Trace m -> m ([SimulationRequest], Trace m)
runRequester spaddr args t = do
  let spr@SPRecord { sp = SP{ requester = req }, srid_seed = seed } = fromJust $ lookupSPR spaddr t
  (reqs, seed') <- runUniqueSourceT (req args) seed
  let trace' = insertSPR spaddr spr{ srid_seed = seed' } t
  return (reqs, trace')
