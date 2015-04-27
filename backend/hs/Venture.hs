{-# LANGUAGE TemplateHaskell #-}
{-# LANGUAGE RankNTypes #-}
{-# LANGUAGE ConstraintKinds #-}

module Venture where

import qualified Data.Map as M
import Control.Monad.Trans.Class
import Control.Monad.Trans.State.Strict
import Control.Monad.Trans.Writer.Strict
import Control.Monad.Random hiding (randoms) -- From cabal install MonadRandom
import Control.Lens  -- from cabal install lens
import qualified Data.Text as DT
import Text.PrettyPrint -- presumably from cabal install pretty

import Utils
import Language hiding (Exp, Value, Env)
import Trace hiding (empty)
import qualified Trace as T
import Regen
import qualified Detach
import qualified Subproblem
import SP
import qualified Inference as I (resimulation_mh, Selector, Assessable(..))

data Directive num = Assume !DT.Text !(T.Exp num)
                   | Observe !(T.Exp num) !(T.Value num)
                   | Predict !(T.Exp num)
  deriving Show

instance (Show num) => Pretty (Directive num) where
    pp (Assume var exp) = text "assume" <> space <> (text $ DT.unpack var) <> space <> pp exp
    pp (Observe exp val) = text "observe" <> space <> pp exp <> space <> pp val
    pp (Predict exp) = text "predict" <> space <> pp exp

data Model m num =
    Model { _env :: !Env
          , _trace :: !(Trace m num)
          -- Hm.  Do I actually need to explicitly track this, or can
          -- it be deduced from the underlying Env and Trace?
          , _directives :: !(M.Map Address (Directive num))
          }

makeLenses ''Model

empty :: Model m num
empty = Model Toplevel T.empty M.empty

initial :: (MonadRandom m, Show num, Real num, Floating num, Enum num) => Model m num
initial = Model e t M.empty where
  (e, t) = runState (initializeBuiltins Toplevel) T.empty

lookupValue :: Address -> Model m num -> Value num
lookupValue a (Model _ t _) =
    fromJust' "No value at address" $ valueOf
    $ fromJust "Invalid address" $ lookupNode a t

topeval :: (MonadRandom m, Numerical num) => Exp num -> (StateT (Model m num) m) Address
topeval exp = do
  (Model e _ _) <- get
  trace `zoom` (eval prior exp e)

assume :: (MonadRandom m, Numerical num) => DT.Text -> Exp num -> (StateT (Model m num) m) Address
assume var exp = do
  -- TODO This implementation of assume does not permit recursive
  -- functions, because of insufficient indirection to the
  -- environment.
  address <- topeval exp
  env %= Frame (M.fromList [(var, address)])
  directives . at address .= Just (Assume var exp)
  return address

-- Evaluate the expression in the environment (building appropriate
-- structure in the trace), and then constrain its value to the given
-- value (up to chasing down references until a random choice is
-- found).  The constraining appears to consist only in removing that
-- node from the list of random choices.
observe :: (MonadRandom m, Numerical num) => Exp num -> Value num -> (StateT (Model m num) m) Address
observe exp v = do
  address <- topeval exp
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
  directives . at address .= Just (Observe exp v)
  return address

predict :: (MonadRandom m, Numerical num) => Exp num -> (StateT (Model m num) m) Address
predict exp = do
  address <- topeval exp
  directives . at address .= Just (Predict exp)
  return address

runDirective' :: (MonadRandom m, T.Numerical num) =>
                 Directive num -> StateT (Model m num) m T.Address
runDirective' (Assume s e) = assume s e
runDirective' (Observe e v) = observe e v
runDirective' (Predict e) = predict e

runDirective :: (MonadRandom m, T.Numerical num) =>
                Directive num -> StateT (Model m num) m (T.Value num)
runDirective d = do
  addr <- runDirective' d
  gets (lookupValue addr)

sample :: (MonadRandom m, Numerical num) => Exp num -> (Model m num) -> m (Value num)
sample exp model = evalStateT action model where
    action = do
      addr <- topeval exp
      gets $ lookupValue addr

sampleM :: (MonadRandom m, Numerical num) => Exp num -> (StateT (Model m num) m) (Value num)
sampleM exp = do
  model <- get
  val <- lift $ sample exp model
  return val

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

-- TODO: These two words feel overly specific.  What am I actually
-- trying to accomplish by exposing the parts of a selector like this?
select :: (Monad m) => I.Selector m num -> StateT (Model m num) m Subproblem.Scaffold
select (I.Assessable sel _) = trace `zoom` do
                                t <- get
                                s <- lift $ sel t
                                return s

assess :: (Monad m) => I.Selector m num -> Subproblem.Scaffold -> StateT (Model m num) m (LogDensity num)
assess (I.Assessable _ do_assess) scaffold = trace `zoom` do
                                               t <- get
                                               return $ do_assess t scaffold

detach :: (MonadRandom m, Numerical num) =>
          Subproblem.Scaffold -> StateT (Model m num) m (LogDensity num)
detach scaffold = trace `zoom` do
  t <- get
  let (t', logd) = runWriter $ Detach.detach scaffold t
  put t'
  return logd

regen :: (MonadRandom m, Numerical num) =>
         Subproblem.Scaffold -> StateT (Model m num) m (LogDensity num)
regen scaffold = trace `zoom` do
  t <- get
  (t', logd) <- lift $ runWriterT $ Regen.regen scaffold prior t -- TODO Expose choice of proposal distribution?
  put t'
  return logd

resimulation_mh :: (MonadRandom m, Numerical num) => I.Selector m num -> StateT (Model m num) m ()
resimulation_mh select = trace `zoom` I.resimulation_mh select
