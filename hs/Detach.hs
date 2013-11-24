module Detach where

import qualified Data.Set as S
import Data.Maybe
import Control.Monad.Reader
import Control.Monad.Trans.Writer.Strict
import Control.Monad.Trans.State.Lazy hiding (state)

import Utils hiding (fromJust)
import Language
import qualified InsertionOrderedSet as O
import Trace

type DRG = O.Set Address
type Absorbers = O.Set Address

data Scaffold = Scaffold { drg :: DRG
                         , absorbers :: Absorbers
                         , brush :: S.Set Address
                         }

scaffold_from_principal_node :: Address -> Reader (Trace m) Scaffold
scaffold_from_principal_node a = do
  (erg, absorbers) <- execStateT (collectERG [(a,True)]) (O.empty, O.empty)
  (brush, (drg, absorbers')) <- runStateT collectBrush (erg, absorbers)
  return $ Scaffold drg absorbers brush

collectERG :: [(Address,Bool)] -> StateT (DRG, Absorbers) (Reader (Trace m)) ()
collectERG [] = return ()
collectERG ((a,principal):as) = do
  member <- gets $ O.member a . fst
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
         opMember <- gets $ O.member opa . fst
         if opMember then resampling a
         else do
           opCanAbsorb <- lift $ asks $ (canAbsorb node) . fromJust . operator node
           if (not principal && opCanAbsorb) then absorbing a
           else resampling a -- TODO check esrReferenceCanAbsorb
  where resampling :: Address -> StateT (DRG, Absorbers) (Reader (Trace m)) ()
        resampling a = do
          modify $ mapSnd $ O.delete a
          modify $ mapFst $ O.insert a
          as' <- lift $ asks $ children a
          collectERG $ (zip as' $ repeat False) ++ as
        absorbing :: Address -> StateT (DRG, Absorbers) (Reader (Trace m)) ()
        absorbing a = do
          modify $ mapSnd $ O.insert a
          collectERG as

collectBrush = undefined

detach :: Scaffold -> Trace rand -> Writer LogDensity (Trace rand)
detach = undefined
