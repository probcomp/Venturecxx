{-# LANGUAGE TemplateHaskell, DoAndIfThenElse #-}
{-# LANGUAGE TupleSections #-}

module Subproblem where

import Control.Lens hiding (children)
import Control.Monad.Reader
import Control.Monad.Trans.State.Lazy
import qualified Data.Map as M
import qualified Data.Set as S
import Text.PrettyPrint hiding (empty) -- presumably from cabal install pretty

import Utils
import qualified InsertionOrderedSet as O
import Trace hiding (empty)

data Scaffold = Scaffold { _principal :: [Address]
                         , _drg :: O.Set Address -- Includes the principal nodes
                         , _absorbers :: O.Set Address
                         , _dead_reqs :: [(SPAddress, [SRId])]
                         , _brush :: S.Set Address
                         }
  deriving Show

makeLenses ''Scaffold

empty :: [Address] -> Scaffold
empty as = Scaffold as O.empty O.empty [] S.empty

instance Pretty Scaffold where
    pp s = hang (text "Scaffold") 1 $
             hang (text "DRG") 1 (pp $ s^.drg) $$
             hang (text "Absorbers") 1 (pp $ s^.absorbers) $$
             hang (text "Brush") 1 (pp $ s^.brush)

scaffold_from_principal_nodes :: [Address] -> Reader (Trace m num) Scaffold
scaffold_from_principal_nodes as = do
  scaffold <- execStateT (collectERG (map (,Nothing) as)) $ empty as
  (_, scaffold', _) <- execStateT (collectBrush $ O.toList $ scaffold ^. drg)
                                  (M.empty, scaffold, S.empty)
  return $ scaffold'

collectERG :: [(Address,Maybe Address)] -> StateT Scaffold (Reader (Trace m num)) ()
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
  where resampling :: Address -> StateT Scaffold (Reader (Trace m num)) ()
        resampling a = do
          absorbers %= O.delete a
          drg %= O.insert a
          as' <- asks $ children a
          collectERG $ (zip as' $ repeat $ Just a) ++ as
        absorbing :: Address -> StateT Scaffold (Reader (Trace m num)) ()
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
collectBrush :: [Address] -> StateT ((M.Map Address Int), Scaffold, S.Set Address)
                                    (Reader (Trace m num)) ()
collectBrush = mapM_ disableRequests where
    -- Given the address of an ERG node, account for the fact that it
    -- ceases making any requests it may have been making (only
    -- relevant to Requester nodes).
    disableRequests :: Address -> StateT ((M.Map Address Int), Scaffold, S.Set Address)
                                         (Reader (Trace m num)) ()
    disableRequests a = do
      member <- use $ _3 . contains a
      if member then return ()
      else do
        _3 . contains a .= True
        node <- view $ nodes . hardix "Disabling requests of non-existent node" a
        case node of
          (Request (Just reqs) _ opa _) -> do
            spaddr <- asks $ fromJust "Disabling requests of operator-less request node"
                             . fromValueAt opa
            answers <- (asks $ fulfilments a)
            sequence_ $ zipWith (disableRequestFor spaddr) (map srid reqs) answers
          _ -> return ()
    -- Given the address of a requested node (and the SPAddress/SRId
    -- path of the request) account for the fact that it is now
    -- requested one time less.
    disableRequestFor :: SPAddress -> SRId -> Address ->
                         StateT ((M.Map Address Int), Scaffold, S.Set Address)
                                (Reader (Trace m num)) ()
    disableRequestFor spaddr srid a = do
      _1 . at a %= maybeSucc
      disabled <- use $ _1 . hardix "Disabling request for a node that has never been disabled" a
      requested <- asks $ numRequests a
      if disabled > requested then
          error $ "Request disablement overcounting bug " ++ (show disabled) ++ " "
                  ++ (show requested) ++ " " ++ (show $ pp a)
      else if disabled == requested then do
          _2 . dead_reqs %= ((spaddr,[srid]):)
          disableFamily a
      else return ()
    -- Given the address of a node that is no longer requested, put it
    -- and its entire family in the brush.
    disableFamily :: Address -> StateT ((M.Map Address Int), Scaffold, S.Set Address)
                                       (Reader (Trace m num)) ()
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

