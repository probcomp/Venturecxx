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

-- Return Just the address of the directive if it's a predict, otherwise Nothing
executeDirective :: (MonadRandom m, T.Numerical num) =>
                    V.Directive num -> StateT (V.Model m num) m (Maybe T.Address)
executeDirective (V.Assume s e) = V.assume s e >> return Nothing
executeDirective (V.Observe e v) = V.observe e v >> return Nothing
executeDirective (V.Predict e) = V.predict e >>= return . Just

-- Returns the list of addresses the model wants watched (to wit, the predicts)
execute :: (MonadRandom m, T.Numerical num) => [V.Directive num] -> StateT (V.Model m num) m [T.Address]
execute ds = liftM catMaybes $ mapM executeDirective ds


runDirective' :: (MonadRandom m, T.Numerical num) =>
                 V.Directive num -> StateT (V.Model m num) m (Maybe T.Address)
runDirective' (V.Assume s e) = V.assume s e >>= return . Just
runDirective' (V.Observe e v) = V.observe e v >> return Nothing
runDirective' (V.Predict e) = V.predict e >>= return . Just

runDirective :: (MonadRandom m, T.Numerical num) =>
                V.Directive num -> StateT (V.Model m num) m (Maybe (T.Value num))
runDirective d = do
  addr <- runDirective' d
  case addr of
    Nothing -> return Nothing
    Just a -> gets (Just . (V.lookupValue a))
