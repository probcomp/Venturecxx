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
    undefined

collectBrush = undefined

detach :: Scaffold -> Trace rand -> Writer LogDensity (Trace rand)
detach = undefined
