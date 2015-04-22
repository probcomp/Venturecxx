{-# LANGUAGE ConstraintKinds #-}

-- An interpreter for the inference language, to be used for
-- implementing Venture-as-a-web-server (and maybe a standalone
-- language).

module InferenceInterpreter where

import Control.Monad
import Control.Monad.Random hiding (randoms) -- From cabal install MonadRandom
import Control.Monad.Trans.State.Lazy
import Data.Maybe hiding (fromJust)

import qualified Venture as V
import qualified Trace as T

runDirective' :: (MonadRandom m, T.Numerical num) =>
                 V.Directive num -> StateT (V.Model m num) m T.Address
runDirective' (V.Assume s e) = V.assume s e
runDirective' (V.Observe e v) = V.observe e v
runDirective' (V.Predict e) = V.predict e

runDirective :: (MonadRandom m, T.Numerical num) =>
                V.Directive num -> StateT (V.Model m num) m (T.Value num)
runDirective d = do
  addr <- runDirective' d
  gets (V.lookupValue addr)
