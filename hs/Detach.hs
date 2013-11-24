module Detach where

import qualified Data.Set as S
import Data.Maybe
import Control.Monad.Reader
import Control.Monad.Trans.Writer.Strict
import Control.Monad.Trans.State.Lazy hiding (state)

import Language
import qualified InsertionOrderedSet as O
import Trace

data Scaffold = Scaffold { drg :: O.Set Address
                         , brush :: S.Set Address
                         }

scaffold_from_principal_node :: Address -> Reader (Trace m) Scaffold
scaffold_from_principal_node a = do
  erg <- execStateT (collectERG [(a,True)]) O.empty
  (brush, drg) <- runStateT collectBrush erg
  return $ Scaffold drg brush

collectERG :: [(Address,Bool)] -> StateT (O.Set Address) (Reader (Trace m)) ()
collectERG [] = return ()
collectERG ((a,principal):as) = do
  member <- gets $ O.member a
  if member then collectERG as
  else do
    node <- lift $ asks $ fromJust . lookupNode a
    case node of
      (Constant _) -> error "Constant node should never appear in the DRG"
      (Reference _ _) -> resampling a
      _ -> do
         let opa = fromJust $ opAddr node
         opMember <- gets $ O.member opa -- N.B. This can change as more graph structure is traversed
         if opMember then resampling a
         else do
           opCanAbsorb <- undefined
           if (not principal && opCanAbsorb) then absorbing a
           else resampling a -- TODO check esrReferenceCanAbsorb
  where absorbing = undefined
        resampling = undefined

collectBrush = undefined

detach :: Scaffold -> Trace rand -> Writer LogDensity (Trace rand)
detach = undefined
