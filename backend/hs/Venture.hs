module Venture where

import qualified Data.Map as M
import qualified Data.Set as S
import Control.Monad.Reader
import Control.Monad.Trans.State.Lazy
import Control.Monad.Trans.Writer.Strict
import Control.Monad.Trans.Class
import Control.Monad.Random hiding (randoms) -- From cabal install MonadRandom
import Control.Lens -- From cabal install lens

import Language hiding (Exp, Value, Env)
import Trace
import Regen
import Detach hiding (empty)
import qualified Detach as D (empty)
import SP
import Utils (fromJust)

type Kernel m a = a -> WriterT LogDensity m a

mix_mh_kernels :: (Monad m) => (a -> m ind) -> (a -> ind -> LogDensity) ->
                  (ind -> Kernel m a) -> (Kernel m a)
mix_mh_kernels sampleIndex measureIndex paramK x = do
  ind <- lift $ sampleIndex x
  let ldRho = measureIndex x ind
  tell ldRho
  x' <- paramK ind x
  let ldXi = measureIndex x' ind
  tell $ log_density_negate ldXi
  return x'

metropolis_hastings :: (MonadRandom m) => Kernel m a -> a -> m a
metropolis_hastings propose x = do
  (x', (LogDensity alpha)) <- runWriterT $ propose x
  u <- getRandomR (0.0,1.0)
  if (log u < alpha) then
      return x'
  else
      return x

-- TODO Is this a standard combinator too?
modifyM :: Monad m => (s -> m s) -> StateT s m ()
modifyM act = get >>= (lift . act) >>= put

scaffold_mh_kernel :: (MonadRandom m) => Scaffold -> Kernel m (Trace m)
scaffold_mh_kernel scaffold trace = do
  torus <- censor log_density_negate $ stupid $ detach scaffold trace
  regen scaffold (traceShowTrace torus torus)
        where stupid :: (Monad m) => Writer w a -> WriterT w m a
              stupid = WriterT . return . runWriter

principal_node_mh :: (MonadRandom m) => Kernel m (Trace m)
principal_node_mh = mix_mh_kernels sample log_density scaffold_mh_kernel where
    sample :: (MonadRandom m) => Trace m -> m Scaffold
    sample trace =
        if trace^.randoms.to S.size == 0 then return D.empty
        else do
          index <- getRandomR (0, trace^.randoms.to S.size - 1)
          return $ runReader (scaffold_from_principal_node ((trace^.randoms.to S.toList) !! index)) trace

    log_density :: Trace m -> a -> LogDensity
    log_density t _ = LogDensity $ -log(fromIntegral $ t^.randoms.to S.size)

data Directive = Assume String Exp
               | Observe Exp Value

assume :: (MonadRandom m) => String -> Exp -> StateT Env (StateT (Trace m) m) ()
assume var exp = do
  -- TODO This implementation of assume does not permit recursive
  -- functions, because of insufficient indirection to the
  -- environment.
  env <- get
  address <- lift $ eval exp env
  modify $ Frame (M.fromList [(var, address)])

-- Evaluate the expression in the environment (building appropriate
-- structure in the trace), and then constrain its value to the given
-- value (up to chasing down references until a random choice is
-- found).  The constraining appears to consist only in removing that
-- node from the list of random choices.
observe :: (MonadRandom m) => Exp -> Value -> ReaderT Env (StateT (Trace m) m) ()
observe exp v = do
  env <- ask
  address <- lift $ eval exp env
  -- TODO What should happen if one observes a value that had
  -- (deterministic) consequences, e.g.
  -- (assume x (normal 1 1))
  -- (assume y (+ x 1))
  -- (observe x 1)
  -- After this, the trace is presumably in an inconsistent state,
  -- from which it in fact has no way to recover.  As of the present
  -- writing, Venturecxx has this limitation as well, so I will not
  -- address it here.
  lift $ modify $ constrain address v

execute :: (MonadRandom m) => [Directive] -> StateT (Trace m) m ()
execute ds = runStateT_ (do
  modifyM initializeBuiltins
  mapM_ executeOne ds) Toplevel where
    -- executeOne :: Directive -> StateT Env (StateT (Trace m) m) ()
    executeOne (Assume s e) = assume s e
    executeOne (Observe e v) = get >>= lift . runReaderT (observe e v)
    runStateT_ act s = (runStateT act s) >> return ()


watching_infer :: (MonadRandom m) => Address -> Int -> StateT (Trace m) m [Value]
watching_infer address ct = replicateM ct (do
  t <- get
  modifyM $ liftM (traceShowTrace t) $ metropolis_hastings principal_node_mh
  gets $ fromJust "Value was not restored by inference" . valueOf
         . fromJust "Address became invalid after inference" . (lookupNode address))

simulation :: (MonadRandom m) => Int -> Exp -> StateT (Trace m) m [Value]
simulation ct exp = do
  env <- initializeBuiltins Toplevel
  address <- eval exp env
  watching_infer address ct

simulate_soup :: (MonadRandom m) => Int -> Exp -> m [Value]
simulate_soup ct exp = evalStateT (simulation ct exp) empty

-- simulate_soup 1 $ Datum $ Number 1.0
-- simulate_soup 1 $ App (Lam ["x"] (Variable "x")) [(Datum $ Number 1.0)]
-- (let (id ...) (id 1))
-- simulate_soup 1 $ App (Lam ["id"] (App (Variable "id") [(Datum $ Number 1.0)])) [(Lam ["x"] (Variable "x"))]
-- K combinator
-- simulate_soup 1 $ App (App (Lam ["x"] (Lam ["y"] (Variable "x"))) [(Datum $ Number 1.0)]) [(Datum $ Number 2.0)]
-- simulate_soup 10 $ App (Variable "bernoulli") []
-- simulate_soup 10 $ App (Variable "normal") [(Datum $ Number 0.0), (Datum $ Number 2.0)]
-- simulate_soup 10 $ App (App (Variable "select") [(App (Variable "bernoulli") []), (Lam [] (Datum $ Number 1.0)), (Lam [] (Datum $ Number 2.0))]) []

-- Next subgoal: Do MH inference with observations on some trivial
--   programs (e.g. normal with normally distributed mean?)
--   - also involving brush

-- Eventual goals
-- - Built-in SPs with collapsed exchangeably coupled state
--   - This imposes the ordering requirement on regen and detach
--   - This is where incorporate and unincorporate (remove) come from

-- Non-goals
-- - Latent simulation kernels for SPs
--   - This seems to be the only source of nonzero weights in {regen,detach}Internal
--     (also eval and uneval (detachFamily?))
-- - Absorbing At Applications (I don't even understand the machinery this requires)
