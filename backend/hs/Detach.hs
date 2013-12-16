{-# Language TemplateHaskell, DoAndIfThenElse #-}

module Detach where

import qualified Data.Set as S
import qualified Data.Map as M
import Control.Monad.Reader
import Control.Monad.Trans.Writer.Strict
import Control.Monad.Trans.State.Lazy
import Control.Lens hiding (children)
import Text.PrettyPrint hiding (empty) -- presumably from cabal install pretty

import Utils
import Language
import qualified InsertionOrderedSet as O
import Trace hiding (empty)

data Scaffold = Scaffold { _drg :: O.Set Address
                         , _absorbers :: O.Set Address
                         , _dead_reqs :: [(SPAddress, [SRId])]
                         , _brush :: S.Set Address
                         -- TODO If I don't keep track somewhere, I
                         -- will leak SPRecords under detach and
                         -- regen.
                         }
  deriving Show

makeLenses ''Scaffold

empty :: Scaffold
empty = Scaffold O.empty O.empty [] S.empty

instance Pretty Scaffold where
    pp s = hang (text "Scaffold") 1 $
             hang (text "DRG") 1 (pp $ s^.drg) $$
             hang (text "Absorbers") 1 (pp $ s^.absorbers) $$
             hang (text "Brush") 1 (pp $ s^.brush)

scaffold_from_principal_node :: Address -> Reader (Trace m) Scaffold
scaffold_from_principal_node a = do
  scaffold <- execStateT (collectERG [(a,Nothing)]) empty
  (_, scaffold', _) <- execStateT (collectBrush $ O.toList $ scaffold ^. drg) (M.empty, scaffold, S.empty)
  return $ scaffold'

collectERG :: [(Address,Maybe Address)] -> StateT Scaffold (Reader (Trace m)) ()
collectERG [] = return ()
collectERG ((a,erg_parent):as) = do
  -- erg_parent == Nothing means this is a principal node
  member <- uses drg $ O.member a
  -- Not stopping on nodes that are already absorbers because they can become ERG nodes
  -- (if I discover that their operator is in the ERG after all)
  if member then collectERG as
  else do
    node <- view $ nodes . hardix "Collecting a nonexistent node into the ERG" a
    case node of
      (Constant _) -> error "Constant node should never appear in the ERG"
      (Reference _ _) -> resampling a
      _ -> case erg_parent of
             Nothing -> resampling a -- principal node
             (Just p_addr) -> do
               opCanAbsorb <- lift $ asks $ (canAbsorb node p_addr)
                              . fromJust "ERGing application node with no operator" . operator node
               if opCanAbsorb then absorbing a
               else resampling a
  where resampling :: Address -> StateT Scaffold (Reader (Trace m)) ()
        resampling a = do
          absorbers %= O.delete a
          drg %= O.insert a
          as' <- asks $ children a
          collectERG $ (zip as' $ repeat $ Just a) ++ as
        absorbing :: Address -> StateT Scaffold (Reader (Trace m)) ()
        absorbing a = do
          absorbers %= O.insert a
          collectERG as

-- Given the list of addresses in the ERG, produce an updated scaffold
-- that includes the brush (and whose drg field is the actual DRG, not
-- the ERG).
-- The brush is those nodes that become no longer requested by
-- anything after the requests made by requester nodes in the DRG are
-- retracted.  I compute them using a reference-counting scheme: The
-- first field of the state is the number of requests for any given
-- address that have been disabled, and the third field of the state
-- is the set addresses the disablement of whose outgoing requests is
-- already under way.
collectBrush :: [Address] -> StateT ((M.Map Address Int), Scaffold, S.Set Address) (Reader (Trace m)) ()
collectBrush = mapM_ disableRequests where
    -- Given the address of an ERG node, account for the fact that it
    -- ceases making any requests it may have been making (only
    -- relevant to Requester nodes).
    disableRequests :: Address -> StateT ((M.Map Address Int), Scaffold, S.Set Address) (Reader (Trace m)) ()
    disableRequests a = do
      member <- use $ _3 . contains a
      if member then return ()
      else do
        _3 . contains a .= True
        node <- view $ nodes . hardix "Disabling requests of non-existent node" a
        case node of
          (Request (Just reqs) _ _ _) -> do
            spaddr <- asks $ fromJust "Disabling requests of operator-less request node" . operatorAddr node
            _2 . dead_reqs %= ((spaddr,map srid reqs):)
            (asks $ fulfilments a) >>= (mapM_ disableRequestFor)
          _ -> return ()
    -- Given the address of a requested node, account for the fact
    -- that it is now requested one time less.
    disableRequestFor :: Address -> StateT ((M.Map Address Int), Scaffold, S.Set Address) (Reader (Trace m)) ()
    disableRequestFor a = do
      _1 . at a %= maybeSucc
      disabled <- use $ _1 . hardix "Disabling request for a node that has never been disabled" a
      requested <- asks $ numRequests a
      if disabled > requested then
          error $ "Request disablement overcounting bug " ++ (show disabled) ++ " " ++ (show requested) ++ " " ++ (show $ pp a)
      else if disabled == requested then disableFamily a
      else return ()
    -- Given the address of a node that is no longer requested, put it
    -- and its entire family in the brush.
    disableFamily :: Address -> StateT ((M.Map Address Int), Scaffold, S.Set Address) (Reader (Trace m)) ()
    disableFamily a = do
      markBrush a
      node <- view $ nodes . hardix "Disabling nonexistent family" a
      case node of
        (Output _ reqA opa operands _) -> do
                        markBrush reqA
                        disableRequests reqA
                        disableFamily opa
                        mapM_ disableFamily operands
        _ -> return ()
    markBrush a = do
      _2 . drg %= O.delete a
      _2 . absorbers %= O.delete a
      _2 . brush %= S.insert a

detach' :: Scaffold -> StateT (Trace m) (Writer LogDensity) ()
detach' Scaffold { _drg = d, _absorbers = abs, _dead_reqs = reqs, _brush = bru } = do
  mapM_ absorbAt $ reverse $ O.toList abs
  mapM_ (stupid . eraseValue) $ reverse $ O.toList d
  mapM_ (stupid . forgetRequest) reqs
  mapM_ (stupid . forgetNode) $ reverse $ S.toList bru
  where eraseValue :: Address -> State (Trace m) ()
        eraseValue a = do
          node <- use $ nodes . hardix "Erasing the value of a nonexistent node" a
          do_unincorporate a -- Effective if a is an Output node
          do_unincorporateR a -- Effective if a is a Request node
          nodes . ix a . value .= Nothing
          case node of
            (Request _ (Just outA) _ _) -> responsesAt outA .= []
            _ -> return ()
        forgetRequest :: (SPAddress, [SRId]) -> State (Trace m) ()
        forgetRequest x = modify $ forgetResponses x
        forgetNode :: Address -> State (Trace m) ()
        forgetNode a = do
          do_unincorporate a
          do_unincorporateR a
          modify $ deleteNode a
        stupid :: (Monad m) => State s a -> StateT s m a
        stupid = StateT . (return .) . runState

detach :: Scaffold -> (Trace m) -> Writer LogDensity (Trace m)
detach s t = liftM snd $ runStateT (detach' s) t
