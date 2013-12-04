module Detach where

import qualified Data.Set as S
import qualified Data.Map as M
import Data.Maybe hiding (fromJust)
import Control.Monad.Reader
import Control.Monad.Trans.Writer.Strict
import Control.Monad.Trans.State.Lazy hiding (state)

import Utils
import Language
import qualified InsertionOrderedSet as O
import Trace hiding (empty)

data Scaffold = Scaffold { drg :: O.Set Address
                         , absorbers :: O.Set Address
                         , dead_reqs :: [(SPAddress, [SRId])]
                         , brush :: S.Set Address
                         -- TODO If I don't keep track somewhere, I
                         -- will leak SPRecords under detach and
                         -- regen.
                         }

mapDrg f s@Scaffold{ drg = d } = s{ drg = f d}
mapAbs f s@Scaffold{ absorbers = a } = s{ absorbers = f a}
mapReq f s@Scaffold{ dead_reqs = d } = s{ dead_reqs = f d}
mapBru f s@Scaffold{ brush = b } = s{ brush = f b}

empty :: Scaffold
empty = Scaffold O.empty O.empty [] S.empty


scaffold_from_principal_node :: Address -> Reader (Trace m) Scaffold
scaffold_from_principal_node a = do
  scaffold <- execStateT (collectERG [(a,True)]) empty
  (_, scaffold') <- execStateT (collectBrush $ O.toList $ drg scaffold) (M.empty, scaffold)
  return $ scaffold'

collectERG :: [(Address,Bool)] -> StateT Scaffold (Reader (Trace m)) ()
collectERG [] = return ()
collectERG ((a,principal):as) = do
  member <- gets $ O.member a . drg
  -- Not stopping on nodes that are already absorbers because they can become DRG nodes
  -- (if I discover that their operator is in the DRG after all)
  if member then collectERG as
  else do
    node <- lift $ asks $ fromJust "Collecting a nonexistent node into the DRG" . lookupNode a
    case node of
      (Constant _) -> error "Constant node should never appear in the DRG"
      (Reference _ _) -> resampling a
      _ -> do
         let opa = fromJust "DRGing application node with no operator" $ opAddr node
         -- N.B. This can change as more graph structure is traversed
         opMember <- gets $ O.member opa . drg
         if opMember then resampling a
         else do
           opCanAbsorb <- lift $ asks $ (canAbsorb node)
                          . fromJust "DRGing application node with no operator" . operator node
           if (not principal && opCanAbsorb) then absorbing a
           else resampling a -- TODO check esrReferenceCanAbsorb
  where resampling :: Address -> StateT Scaffold (Reader (Trace m)) ()
        resampling a = do
          modify $ mapAbs $ O.delete a
          modify $ mapDrg $ O.insert a
          as' <- lift $ asks $ children a
          collectERG $ (zip as' $ repeat False) ++ as
        absorbing :: Address -> StateT Scaffold (Reader (Trace m)) ()
        absorbing a = do
          modify $ mapAbs $ O.insert a
          collectERG as

-- Given the list of addresses in the DRG, produce an updated scaffold
-- that includes the brush.  TODO Do I need to read the existing
-- scaffold to do this, or can I get away with returning the brush
-- and the dead_reqs?
-- The brush is those nodes that become no longer requested by anything
-- after the requests made by requester nodes in the DRG are retracted.
-- I compute them using a reference-counting scheme.
collectBrush :: [Address] -> StateT ((M.Map Address Int), Scaffold) (Reader (Trace m)) ()
collectBrush = mapM_ disableRequests where
    -- Given the address of a DRG node, account for the fact that it
    -- ceases making any requests it may have been making (only
    -- relevant to Requester nodes).
    disableRequests :: Address -> StateT ((M.Map Address Int), Scaffold) (Reader (Trace m)) ()
    disableRequests a = do
      node <- asks $ fromJust "Disabling requests of non-existent node" . lookupNode a
      case node of
        (Request (Just reqs) _ _) -> do
          spaddr <- asks $ fromJust "Disabling requests of operator-less request node" . operatorAddr node
          let reqIds = requestIds node
          modify $ mapSnd $ mapReq ((spaddr,reqIds):)
          (asks $ fulfilments a) >>= (mapM_ disableRequestFor)
        _ -> return ()
    -- Given the address of a requested node, account for the fact
    -- that it is now requested one time less.
    disableRequestFor :: Address -> StateT ((M.Map Address Int), Scaffold) (Reader (Trace m)) ()
    disableRequestFor a = do
      modify $ mapFst $ M.alter maybeSucc a
      disabled <- gets $ fromJust "Disabling request for a node that has never been disabled" . M.lookup a . fst
      requested <- asks $ numRequests a
      if disabled == requested then disableFamily a
      else return ()
    -- Given the address of a node that is no longer requested, put it
    -- and its entire family in the brush.
    disableFamily :: Address -> StateT ((M.Map Address Int), Scaffold) (Reader (Trace m)) ()
    disableFamily a = do
      brush a
      node <- asks $ fromJust "Disabling nonexistent family" . lookupNode a
      case node of
        (Output _ reqA opa operands _) -> do
                        brush reqA
                        disableRequests reqA
                        disableFamily opa
                        mapM_ disableFamily operands
        _ -> return ()
    brush a = do
      modify $ mapSnd $ mapDrg $ O.delete a
      modify $ mapSnd $ mapAbs $ O.delete a
      modify $ mapSnd $ mapBru $ S.insert a

    maybeSucc Nothing = Just 1
    maybeSucc (Just x) = Just $ x+1

detach' :: Scaffold -> StateT (Trace m) (Writer LogDensity) ()
detach' Scaffold { drg = d, absorbers = abs, dead_reqs = reqs, brush = bru } = do
  mapM_ unabsorbValue $ reverse $ O.toList abs
  mapM_ (stupid . eraseValue) $ O.toList d
  mapM_ (stupid . forgetRequest) reqs
  mapM_ (stupid . forgetNode) $ S.toList bru
  where unabsorbValue :: Address -> StateT (Trace m) (Writer LogDensity) ()
        unabsorbValue a = do
          node <- gets $ fromJust "Unabsorbing non-existent node" . lookupNode a
          sp <- gets $ fromJust "Unabsorbing node with no operator" . operator node
          wt <- gets $ absorb node sp
          lift $ tell $ LogDensity wt
        eraseValue :: Address -> State (Trace m) ()
        eraseValue a = modify $ adjustNode devalue a
        forgetRequest :: (SPAddress, [SRId]) -> State (Trace m) ()
        forgetRequest x = modify $ forgetResponses x
        forgetNode :: Address -> State (Trace m) ()
        forgetNode a = modify $ deleteNode a
        stupid :: (Monad m) => State s a -> StateT s m a
        stupid = StateT . (return .) . runState

detach :: Scaffold -> (Trace m) -> Writer LogDensity (Trace m)
detach s t = liftM snd $ runStateT (detach' s) t
