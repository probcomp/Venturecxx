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

data Directive = Assume String T.Exp
               | Observe T.Exp T.Value
               | Predict T.Exp
  deriving Show

-- Return Just the address of the directive if it's a predict, otherwise Nothing
executeDirective :: (MonadRandom m) => Directive -> StateT (V.Model m) m (Maybe T.Address)
executeDirective (Assume s e) = V.assume s e >> return Nothing
executeDirective (Observe e v) = V.observe e v >> return Nothing
executeDirective (Predict e) = V.predict e >>= return . Just

-- Returns the list of addresses the model wants watched (to wit, the predicts)
execute :: (MonadRandom m) => [Directive] -> StateT (V.Model m) m [T.Address]
execute ds = liftM catMaybes $ mapM executeDirective ds


runDirective' :: (MonadRandom m) => Directive -> StateT (V.Model m) m (Maybe T.Address)
runDirective' (Assume s e) = V.assume s e >>= return . Just
runDirective' (Observe e v) = V.observe e v >> return Nothing
runDirective' (Predict e) = V.predict e >>= return . Just

runDirective :: (MonadRandom m) => Directive -> StateT (V.Model m) m (Maybe T.Value)
runDirective d = do
  addr <- runDirective' d
  case addr of
    Nothing -> return Nothing
    Just a -> gets (Just . (V.lookupValue a))
