{-# LANGUAGE ConstraintKinds #-}

module Detach where

import Control.Lens hiding (children)
import Control.Monad.Trans.State.Lazy
import Control.Monad.Trans.Writer.Strict
import qualified Data.Set as S

import Utils
import Language
import qualified InsertionOrderedSet as O
import Trace hiding (empty)
import Subproblem

detach' :: (Numerical num) => Scaffold -> StateT (Trace m num) (Writer (LogDensity num)) ()
detach' Scaffold { _drg = d, _absorbers = abs, _dead_reqs = reqs, _brush = bru } = do
  mapM_ absorbAt $ reverse $ O.toList abs
  mapM_ (returnT . eraseValue) $ reverse $ O.toList d
  mapM_ (returnT . forgetRequest) reqs
  mapM_ (returnT . forgetNode) $ reverse $ S.toList bru
  where eraseValue :: (Numerical num) => Address -> State (Trace m num) ()
        eraseValue a = do
          node <- use $ nodes . hardix "Erasing the value of a nonexistent node" a
          do_unincorporate a -- Effective if a is an Output node
          do_unincorporateR a -- Effective if a is a Request node
          nodes . ix a . value .= Nothing
          case node of
            (Request _ (Just outA) _ _) -> responsesAt outA .= []
            _ -> return ()
        forgetRequest :: (SPAddress, [SRId]) -> State (Trace m num) ()
        forgetRequest x = modify $ forgetResponses x
        forgetNode :: (Numerical num) => Address -> State (Trace m num) ()
        forgetNode a = do
          do_unincorporate a
          do_unincorporateR a
          modify $ deleteNode a

detach :: (Numerical num) => Scaffold -> (Trace m num) -> Writer (LogDensity num) (Trace m num)
detach s = execStateT (detach' s)
