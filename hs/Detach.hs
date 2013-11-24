module Detach where

import qualified Data.Set as S
import qualified Data.Map as M
import Data.Maybe
import Control.Monad.Reader
import Control.Monad.Trans.Writer.Strict
import Control.Monad.Trans.State.Lazy hiding (state)

import Utils hiding (fromJust)
import Language
import qualified InsertionOrderedSet as O
import Trace hiding (empty)

type DRG = O.Set Address
type Absorbers = O.Set Address

data Scaffold = Scaffold { drg :: DRG
                         , absorbers :: Absorbers
                         , brush :: S.Set Address
                         }

mapDrg f s@Scaffold{ drg = d } = s{ drg = f d}
mapAbs f s@Scaffold{ absorbers = a } = s{ absorbers = f a}
mapBru f s@Scaffold{ brush = b } = s{ brush = f b}

empty :: Scaffold
empty = Scaffold O.empty O.empty S.empty

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
    node <- lift $ asks $ fromJust . lookupNode a
    case node of
      (Constant _) -> error "Constant node should never appear in the DRG"
      (Reference _ _) -> resampling a
      _ -> do
         let opa = fromJust $ opAddr node
         -- N.B. This can change as more graph structure is traversed
         opMember <- gets $ O.member opa . drg
         if opMember then resampling a
         else do
           opCanAbsorb <- lift $ asks $ (canAbsorb node) . fromJust . operator node
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

collectBrush :: [Address] -> StateT ((M.Map Address Int), Scaffold) (Reader (Trace m)) ()
collectBrush = mapM_ disableRequests where
    disableRequests :: Address -> StateT ((M.Map Address Int), Scaffold) (Reader (Trace m)) ()
    disableRequests a = do
      node <- asks $ fromJust . lookupNode a
      case node of
        (Request (Just reqs) _ _) -> (asks $ fulfilments a) >>= (mapM_ disableRequestFor)
        _ -> return ()
    disableRequestFor :: Address -> StateT ((M.Map Address Int), Scaffold) (Reader (Trace m)) ()
    disableRequestFor a = do
      modify $ mapFst $ M.alter maybeSucc a
      disabled <- gets $ fromJust . M.lookup a . fst
      requested <- asks $ numRequests a
      if disabled == requested then disableFamily a
      else return ()
    disableFamily :: Address -> StateT ((M.Map Address Int), Scaffold) (Reader (Trace m)) ()
    disableFamily a = do
      brush a
      node <- asks $ fromJust . lookupNode a
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

detach :: Scaffold -> Trace rand -> Writer LogDensity (Trace rand)
detach = undefined
