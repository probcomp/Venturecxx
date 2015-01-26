{-# LANGUAGE TemplateHaskell #-}
{-# LANGUAGE RankNTypes #-}

module Engine where

import qualified Data.Map as M
import Control.Monad.Trans.State.Lazy
import Control.Monad.Random hiding (randoms) -- From cabal install MonadRandom
import Control.Lens  -- from cabal install lens

import Utils
import Language hiding (Exp, Value, Env)
import Trace hiding (empty)
import qualified Trace as T
import Regen
import SP

data Model m =
    Model { _env :: Env
           , _trace :: (Trace m)
           }

makeLenses ''Model

empty :: Model m
empty = Model Toplevel T.empty

initial :: (MonadRandom m) => Model m
initial = Model e t where
  (e, t) = runState (initializeBuiltins Toplevel) T.empty

lookupValue :: Address -> Model m -> Value
lookupValue a (Model _ t) =
    fromJust "No value at address" $ valueOf
    $ fromJust "Invalid address" $ lookupNode a t

assume :: (MonadRandom m) => String -> Exp -> (StateT (Model m) m) Address
assume var exp = do
  -- TODO This implementation of assume does not permit recursive
  -- functions, because of insufficient indirection to the
  -- environment.
  (Model e _) <- get
  address <- trace `zoom` (eval exp e)
  env %= Frame (M.fromList [(var, address)])
  return address

-- Evaluate the expression in the environment (building appropriate
-- structure in the trace), and then constrain its value to the given
-- value (up to chasing down references until a random choice is
-- found).  The constraining appears to consist only in removing that
-- node from the list of random choices.
observe :: (MonadRandom m) => Exp -> Value -> (StateT (Model m) m) ()
observe exp v = do
  (Model e _) <- get
  address <- trace `zoom` (eval exp e)
  -- TODO What should happen if one observes a value that had
  -- (deterministic) consequences, e.g.
  -- (assume x (normal 1 1))
  -- (assume y (+ x 1))
  -- (observe x 1)
  -- After this, the trace is presumably in an inconsistent state,
  -- from which it in fact has no way to recover.  As of the present
  -- writing, Venturecxx has this limitation as well, so I will not
  -- address it here.
  trace `zoom` (constrain address v)

predict :: (MonadRandom m) => Exp -> (StateT (Model m) m) Address
predict exp = do
  (Model e _) <- get
  trace `zoom` (eval exp e)

-- TODO Understand the set of layers of abstraction of trace operations:
-- - what invariants does each layer preserve?
-- - quickcheck and/or prove preservation of those invariants
--   - do I want versions of layer operations that check their
--     preconditions and throw errors?
--     - e.g., deleteNode can probably do so at an additive log cost
--       by checking whether the node to be deleted is referenced.
--   - consider LiquidHaskell as a proof language
-- - find complete sets of operations at each level, so that a higher
--   level does not need to circumvent the level below it
-- - enforce by module export lists that clients do not circumvent
--   those abstraction boundaries.

-- TODO AAA.  Daniel's explanation for how appears to translate as follows:
-- To cbeta_bernoullii add
--   cbeta_bernoulli_flip (phanY, phanN) (incY, incN) = ... where
--     ctYes = phanY + incY
--     ctNo = phanN + incN
-- etc; also
--   cbeta_bernoulli_log_d_counts :: (phanY, phanN) (incY, incN) = ... -- some double
-- which becomes the weight when detaching or regenning.
-- Daniel says that complexities arise when, e.g., resampling the
-- hyperparameter also causes the set of applications of the made SP to
-- change.
