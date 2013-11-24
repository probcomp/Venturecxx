module Detach where

import qualified Data.Set as S
import Control.Monad.Trans.Writer.Strict

import Language
import qualified InsertionOrderedSet as O
import Trace

data Scaffold = Scaffold { drg :: O.Set Address
                         , brush :: S.Set Address
                         }

scaffold_from_principal_node :: Address -> Trace rand -> Scaffold
scaffold_from_principal_node = undefined

detach :: Scaffold -> Trace rand -> Writer LogDensity (Trace rand)
detach = undefined
