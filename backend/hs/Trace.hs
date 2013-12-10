{-# LANGUAGE FlexibleContexts, TemplateHaskell, TypeSynonymInstances, FlexibleInstances, ExistentialQuantification, RecordWildCards #-}

module Trace where

import Debug.Trace
import Data.Maybe hiding (fromJust)
import qualified Data.Map as M
import qualified Data.Set as S
import Control.Lens  -- from cabal install lens
import Control.Monad.State hiding (state) -- :set -hide-package monads-tf-0.1.0.1
import Control.Monad.Writer.Class
import Text.PrettyPrint -- presumably from cabal install pretty

import Utils
import Language hiding (Value, Exp, Env)
import qualified Language as L

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

srid :: SimulationRequest -> SRId
srid (SimulationRequest id _ _) = id

-- TODO Can I refactor this data type to capture the fact that
-- deterministic requesters and outputters never have meaningful log_d
-- components, whereas stochastic ones may or may not?

-- m is the type of randomness source that this SP uses, presumably an
-- instance of MonadRandom.
-- a is the type of the state that mediates any exchangeable coupling
-- between this SP's outputs.  For most SPs, a = ().  a is existential, per
-- http://www.haskell.org/haskellwiki/Heterogenous_collections#Existential_types
-- because I wish to be able to store SPs in homogeneous data structures.

-- The collection of objects (incorporate v) U (unincorporate v) is
-- expected to form an _Abelian_ group acting on a (except for v on
-- which they error out).  Further, for any given v, (unincorporate v)
-- and (incorporate v) are expected to be inverses.
data SP m = forall a. SP
    { requester :: SPRequester m a
    , log_d_req :: Maybe (a -> [Address] -> [SimulationRequest] -> Double)
    , outputter :: SPOutputter m a
    , log_d_out :: Maybe (a -> [Node] -> [Node] -> Value -> Double)
    , current :: a
    -- TODO Do these guys need to accept the argument lists?
    , incorporate :: Value -> a -> a
    , unincorporate :: Value -> a -> a
    }

-- These functions appear to be necessary to avoid a bizarre compile
-- error in GHC, per
-- http://breaks.for.alienz.org/blog/2011/10/21/record-update-for-insufficiently-polymorphic-field/
do_inc :: Value -> SP m -> SP m
do_inc v SP{..} = SP{ current = incorporate v current, ..}

do_uninc :: Value -> SP m -> SP m
do_uninc v SP{..} = SP{ current = unincorporate v current, ..}

instance Show (SP m) where
    show _ = "A stochastic procedure"

-- TODO Is there a nice way to unify these two data types and their
-- methods?
data SPRequester m a = DeterministicR (a -> [Address] -> UniqueSource [SimulationRequest])
                     | RandomR (a -> [Address] -> UniqueSourceT m [SimulationRequest])

data SPOutputter m a = Trivial
                     | DeterministicO (a -> [Node] -> [Node] -> Value)
                     | RandomO (a -> [Node] -> [Node] -> m Value)
                     | SPMaker (a -> [Node] -> [Node] -> SP m) -- Are these ever random?

asRandomR :: (Monad m) => SPRequester m a -> a -> [Address] -> UniqueSourceT m [SimulationRequest]
asRandomR (RandomR f) st as = f st as
asRandomR (DeterministicR f) st as = returnT $ f st as

isRandomR :: SPRequester m a -> Bool
isRandomR (RandomR _) = True
isRandomR (DeterministicR _) = False

asRandomO :: (Monad m) => SPOutputter m a -> a -> [Node] -> [Node] -> Either (m Value) (SP m)
asRandomO Trivial _ _ (r0:_) = Left $ return $ fromJust "Trivial outputter node had no value" $ valueOf r0
asRandomO Trivial _ _ _ = error "Trivial outputter requires one response"
asRandomO (RandomO f) st args reqs = Left $ f st args reqs
asRandomO (DeterministicO f) st args reqs = Left $ return $ f st args reqs
asRandomO (SPMaker f) st args reqs = Right $ f st args reqs

isRandomO :: SPOutputter m a -> Bool
isRandomO Trivial = False
isRandomO (RandomO _) = True
isRandomO (DeterministicO _) = False
isRandomO (SPMaker _) = False

-- Can the given node, which is an application of the given SP, absorb
-- a change to the given address (which is expected to be one of its
-- parents).
canAbsorb :: Node -> Address -> SP m -> Bool
canAbsorb (Request _ _ opA _)      a _                        | opA  == a = False
canAbsorb (Request _ _ _ _)        _ SP{log_d_req = (Just _)}             = True
canAbsorb (Output _ reqA _ _ _)    a _                        | reqA == a = False
canAbsorb (Output _ _ opA _ _)     a _                        | opA  == a = False
canAbsorb (Output _ _ _ _ (fst:_)) a SP{outputter = Trivial}  | fst  == a = False
canAbsorb (Output _ _ _ _ _)       _ SP{outputter = Trivial}              = True
canAbsorb (Output _ _ _ _ _)       _ SP{log_d_out = (Just _)}             = True
canAbsorb _ _ _ = False

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
    re_requests _ _ = error "Trying to set requests for a non-request node."

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
    _responses _ = []
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
                                       (Just SP{requester = req}) -> isRandomR req
isRandomNode n@(Output _ _ _ _ _) t = case operator n t of
                                        Nothing -> False
                                        (Just SP{outputter = out}) -> isRandomO out
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

addFreshSP :: SP m -> Trace m -> (SPAddress, Trace m)
addFreshSP sp t@Trace{ _sprs = ss, _spaddr_seed = seed } = (a, t{ _sprs = ss', _spaddr_seed = seed'}) where
    (a, seed') = runUniqueSource (liftM SPAddress fresh) seed
    ss' = M.insert a (spRecord sp) ss

fulfilments :: Address -> Trace m -> [Address]
-- The addresses of the responses to the requests made by the Request
-- node at Address.
fulfilments a t = map (fromJust "Unfulfilled request" . flip M.lookup reqs) $ requestIds node where
    node = t ^. nodes . hardix "Asking for fulfilments of a missing node" a
    SPRecord { requests = reqs } = fromJust "Asking for fulfilments of a node with no operator record" $ operatorRecord node t

insertResponse :: SPAddress -> SRId -> Address -> Trace m -> Trace m
insertResponse spa id a t@Trace{ _sprs = ss, _request_counts = r } =
    t{ _sprs = M.insert spa spr' ss, _request_counts = r' } where
        spr' = spr{ requests = M.insert id a reqs }
        spr@SPRecord { requests = reqs } = t ^. sprs . hardix "Inserting response to non-SP" spa
        r' = M.alter succ a r
        succ Nothing = Just 1
        succ (Just n) = Just (n+1)

lookupResponse :: SPAddress -> SRId -> Trace m -> Maybe Address
lookupResponse spa srid t = do
  SPRecord { requests = reqs } <- t ^. sprs . at spa
  M.lookup srid reqs

forgetResponses :: (SPAddress, [SRId]) -> Trace m -> Trace m
forgetResponses (spaddr, srids) t@Trace{ _sprs = ss, _request_counts = r } =
    t{ _sprs = M.insert spaddr spr' ss, _request_counts = r' } where
        spr' = spr{ requests = foldl (flip M.delete) reqs srids }
        spr@SPRecord { requests = reqs } = t ^. sprs . hardix "Forgetting responses to non-SP" spaddr
        r' = foldl decrement r srids
        decrement :: (M.Map Address Int) -> SRId -> (M.Map Address Int)
        decrement m srid = M.update maybePred k m where
            k = fromJust "Forgetting response that isn't there" $ M.lookup srid reqs
            maybePred 1 = Nothing
            maybePred n = Just $ n-1

runRequester :: (Monad m, MonadTrans t, MonadState (Trace m) (t m)) => SPAddress -> [Address] -> t m [SimulationRequest]
runRequester spaddr args = do
  spr@SPRecord { sp = SP{ requester = req, current = a }, srid_seed = seed } <-
      use $ sprs . hardix "Running the requester of a non-SP" spaddr
  (reqs, seed') <- lift $ runUniqueSourceT (asRandomR req a args) seed
  sprs . ix spaddr .= spr{ srid_seed = seed' }
  return reqs

-- How many times has the given address been requested.
numRequests :: Address -> Trace m -> Int
numRequests a t = fromMaybe 0 $ t^.request_counts.at a

-- Nodes in the trace that depend upon the node at the given address.
children :: Address -> Trace m -> [Address]
children a t = t ^. nodeChildren . at a & fromJust "Loooking up the children of a nonexistent node" & S.toList

-- TODO Use of Template Haskell seems to force this to be in the same
-- block of code as lookupNode.
absorb :: Node -> SP m -> Trace m -> Double
absorb (Request (Just reqs) _ _ args) SP{log_d_req = (Just f), current = a} _ = f a args reqs
-- This clause is only right if canAbsorb returned True on all changed parents
absorb (Output _ _ _ _ _) SP { outputter = Trivial } _ = 0
absorb (Output (Just v) _ _ args reqs) SP{log_d_out = (Just f), current = a} t = f a args' reqs' v where
    args' = map (fromJust "absorb" . flip lookupNode t) args
    reqs' = map (fromJust "absorb" . flip lookupNode t) reqs
absorb _ _ _ = error "Inappropriate absorb attempt"

absorbAt :: (MonadState (Trace m1) m, MonadWriter LogDensity m) => Address -> m ()
absorbAt a = do
  node <- use $ nodes . hardix "Absorbing at a nonexistent node" a
  sp <- gets $ fromJust "Absorbing at a node with no operator" . operator node
  wt <- gets $ absorb node sp
  tell $ LogDensity wt

-- (Un)Incorporate the value currently at the given address (from)into
-- its operator using the supplied function (which is expected to be
-- either do_inc or do_uninc).  Only applies to Output nodes.
corporate :: (Value -> SP m -> SP m) -> Address -> Trace m -> Trace m
corporate f a = execState (do
  node <- use $ nodes . hardix "Unincorporating the value of a nonexistent node" a
  case node of
    (Output _ _ _ _ _) -> do
      let v = fromJust "Unincorporating value that isn't there" $ valueOf node
      spaddr <- gets $ fromJust "Unincorporating value for an output with no operator address" . (operatorAddr node)
      sp <- gets $ fromJust "Unincorporating value for an output with no operator" . (operator node)
      sprs . ix spaddr %= \r -> r{sp = f v sp}
    _ -> return ())

do_unincorporate :: Address -> Trace m -> Trace m
do_unincorporate = corporate do_uninc
do_incorporate :: Address -> Trace m -> Trace m
do_incorporate = corporate do_inc

constrain :: Address -> Value -> Trace m -> Trace m
constrain a v = execState (do
  modify $ do_unincorporate a
  nodes . ix a . value .= Just v
  modify $ do_incorporate a
  -- TODO What will cause the node to be re-added to the set of random
  -- choices if the constraint is lifted in the future?
  randoms %= S.delete a
  node <- use $ nodes . hardix "Trying to constrain a non-existent node" a
  case node of
    (Reference _ a') -> modify $ constrain a' v
    (Output _ _ _ _ reqs) -> do
      op <- gets $ operator node
      case op of
        Nothing -> error "Trying to constrain an output node with no operator"
        (Just SP{outputter = Trivial}) ->
           case reqs of
             -- TODO Make sure this constraint gets lifted if the
             -- requester is regenerated, even if r0 is ultimately a
             -- reference to some non-brush node.
             (r0:_) -> modify $ constrain r0 v
             _ -> error "Trying to constrain a trivial output node with no fulfilments"
        _ -> return ()
    _ -> return ())

----------------------------------------------------------------------
-- Invariants that traces ought to obey

-- 1. Every Address should point to a Node, except in the middle of
--    relevant operations (which are what? node insertion and node
--    deletion only?)

-- 2. Every SPAddress should point to an SPRecord, except in the
--    middle of relevant operations (which are what? SP insertion and
--    SP deletion only?)

-- 3. The node children maps should be right, to wit A should be
--    recorded as a child of B iff the address of B appears in the
--    list of parentAddrs of A (except in the middle of node insertion
--    and deletion only?).

-- 4. All Request and Output nodes should come in pairs, determined by
--    the reqA address of the Output node.  Their operator and
--    argument lists should be equal.

-- 5. After any regen, all Request nodes should have pointers to their
--    output nodes (not necessarily during a regen, because the output
--    nodes wish to be created with their fulfilments).

-- 6. The request counts should be right, to wit M.lookup a
--    request_counts should always be Just the number of times a
--    appears as a value in any requests maps of any SPRecords (except
--    when?)

-- 7. The seeds should be right, to wit the _addr_seed should exceed
--    every Address that appears in the trace, the _spaddr_seed should
--    exceed every extant SPAddress that appears in the trace, and the
--    _srid_seed of each SPRecord should exceed every SRId that
--    appears in that SPRecord's requests map.

-- 8. After any detach-regen cycle, all nodes should have values.

-- 9. After any regen, the request parents of any Output node should
--    agree with the requests made by its Request node (through the
--    requests map of the SPRecord of their mutual operator).

-- 10. The _randoms should be the set of modifiable random choices.  A
--     node is a random choice iff it is a Request or Output node, and
--     the corresponding part of the SP that is the operator is
--     actually stochastic.  A random choice is modifiable iff it is
--     not constrained by observations, but the latter is currently
--     not detectable from the trace itself (but modifiable choices
--     are a subset of all choices).

-- 11. A trace constructed during the course of executing directives,
--     or by inference on such a trace, should have no garbage.  To
--     wit, all Addresses and SPAddresses should be reachable via
--     Nodes, SRIds, and SPRecords from the Addresses contained in the
--     global environment, or the Addresses of predictions or
--     observations (that have not been retracted).

-- TODO Define checkers for structural invariants of traces.
-- TODO confirm (quickcheck?) that no sequence of trace operations at
-- the appropriate level of abstraction can produce a trace that
-- violates the structural invariants.  (Is rejection sampling a
-- sensible way to generate conforming traces, or do I need to test
-- long instruction sequences?)

referencedInvalidAddresses :: Trace m -> [Address]
referencedInvalidAddresses t = invalidParentAddresses t
                               ++ invalidRandomChoices t
                               ++ invalidNodeChildrenKeys t
                               ++ invalidNodeChildren t
                               ++ invalidRequestedAddresses t
                               ++ invalidRequestCountKeys t

invalidParentAddresses :: Trace m -> [Address]
invalidParentAddresses t = filter (invalidAddress t) $ concat $ map parentAddrs $ M.elems $ t ^. nodes
invalidRandomChoices :: Trace m -> [Address]
invalidRandomChoices t = filter (invalidAddress t) $ S.toList $ t ^. randoms
invalidNodeChildrenKeys :: Trace m -> [Address]
invalidNodeChildrenKeys t = filter (invalidAddress t) $ M.keys $ t ^. nodeChildren
invalidNodeChildren :: Trace m -> [Address]
invalidNodeChildren t = filter (invalidAddress t) $ concat $ map S.toList $ M.elems $ t ^. nodeChildren
invalidRequestedAddresses :: Trace m -> [Address]
invalidRequestedAddresses t = filter (invalidAddress t) $ concat $ map (M.elems . requests) $ M.elems $ t ^. sprs
invalidRequestCountKeys :: Trace m -> [Address]
invalidRequestCountKeys t = filter (invalidAddress t) $ M.keys $ t ^. request_counts

invalidAddress :: Trace m -> Address -> Bool
invalidAddress t a = not $ isJust $ lookupNode a t

traceShowTrace :: (Trace m) -> (Trace m)
traceShowTrace t = traceShow (pp t) t

instance Pretty Address where
    pp (Address u) = text "A" <> integer (asInteger u)

instance Pretty SPAddress where
    pp (SPAddress u) = text "SPA" <> integer (asInteger u)

instance Pretty SRId where
    pp (SRId u) = text "SR" <> integer (asInteger u)

instance Pretty (Trace m) where
    pp t = hang (text "Trace") 1 $
             hang (text "Problems") 1 problems $$
             hang (text "Content") 1 contents $$
             hang (text "SPs") 1 sps where
      problems = pp $ referencedInvalidAddresses t -- Add other structural faults as I start detecting them
      contents = sep $ map entry $ M.toList $ t^.nodes
      sps = sep $ map entryS $ M.toList $ t^.sprs
      entry (k,v) = pp k <> colon <> rmark <> pp v
          where rmark = if S.member k $ t^.randoms then text " (R) "
                        else space
      entryS (k,v) = pp k <> colon <+> pp v

instance Pretty Node where
    pp (Constant v) = text "Constant" <+> (parens $ pp v)
    pp (Reference v a) = text "Reference" <+> (parens $ ppDefault "No value" v) <+> pp a
    pp (Request srs outA opA args) =
        text "Request" <+> ppDefault "(No requests)" srs
                 $$ text "out:" <+> ppDefault "none" outA
                 <+> text "oper:" <+> pp opA
                 <+> text "args:" <+> pp args
    pp (Output v reqA opA args reqs) =
        text "Output" <+> parens (ppDefault "No value" v)
                 <+> text "req:" <+> pp reqA
                 <+> text "oper:" <+> pp opA
                 <+> text "args:" <+> pp args
                 <+> text "esrs:" <+> pp reqs

ppDefault :: Pretty a => String -> Maybe a -> Doc
ppDefault _ (Just a) = pp a
ppDefault d Nothing = text d

instance Pretty (SPRecord m) where
    pp SPRecord { requests = rs } = brackets $ sep $ map entry $ M.toList rs where
      entry (k,v) = pp k <> colon <> space <> pp v

instance Pretty Value where
    pp (Number d) = double d
    pp (Symbol s) = text s
    pp (List l) = pp l
    pp (Procedure a) = text "Procedure" <+> pp a
    pp (Boolean True) = text "true"
    pp (Boolean False) = text "false"

instance Pretty SimulationRequest where
    pp (SimulationRequest id exp env) = pp id <+> pp exp $$ pp env

instance Pretty Exp where
    pp = text . show

instance Pretty Env where
    pp e = brackets $ sep $ map entry $ M.toList $ effectiveEnv e where
      entry (k,v) = text k <> colon <> space <> pp v
