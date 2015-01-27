{-# LANGUAGE DoAndIfThenElse #-}

module Inference where

import qualified Data.Set as S
import Control.Monad.Reader
import Control.Monad.Trans.State.Lazy
import Control.Monad.Trans.Writer.Strict
import Control.Monad.Random hiding (randoms) -- From cabal install MonadRandom
import Control.Lens -- From cabal install lens

import Utils
import Language hiding (Exp, Value, Env)
import Trace
import Regen
import Detach
import qualified Subproblem as Sub

type MHAble m a = a -> WriterT LogDensity m a

data Assessable m a b = Assessable (a -> m b) (a -> b -> LogDensity)

metropolis_hastings :: (MonadRandom m) => MHAble m a -> a -> m a
metropolis_hastings propose x = do
  (x', (LogDensity alpha)) <- runWriterT $ propose x
  u <- getRandomR (0.0,1.0)
  if (log u < alpha) then
      return x'
  else
      return x

mix_mh :: (Monad m) => (Assessable m a ind) -> (ind -> MHAble m a) -> (MHAble m a)
mix_mh (Assessable sample measure) param_propose x = do
  ind <- lift $ sample x
  let ldRho = measure x ind
  tell $ log_density_negate ldRho
  x' <- param_propose ind x
  let ldXi = measure x' ind
  tell ldXi
  return x'

scaffold_resimulation_mh :: (MonadRandom m) => Sub.Scaffold -> MHAble m (Trace m)
scaffold_resimulation_mh scaffold trace = do
  torus <- censor log_density_negate $ returnT $ detach scaffold trace
  regen scaffold prior torus

type Selector m = Assessable m (Trace m) Sub.Scaffold

default_one :: (MonadRandom m) => Selector m
default_one = (Assessable sample log_density) where
    sample :: (MonadRandom m) => Trace m -> m Sub.Scaffold
    sample trace =
        if trace^.randoms.to S.size == 0 then return $ Sub.empty []
        else do
          index <- getRandomR (0, trace^.randoms.to S.size - 1)
          let addr = (trace^.randoms.to S.toList) !! index
          let scaffold = runReader (Sub.scaffold_from_principal_nodes [addr]) trace
          return $ scaffold

    log_density :: Trace m -> Sub.Scaffold -> LogDensity
    log_density t _ = LogDensity $ -log(fromIntegral $ t^.randoms.to S.size)

default_all :: (Monad m) => Selector m
default_all = (Assessable sample log_density) where
    sample trace = return $ runReader (Sub.scaffold_from_principal_nodes (trace ^. randoms . to S.toList)) trace
    log_density _ _ = LogDensity 0

resimulation_mh :: (MonadRandom m) => Selector m -> StateT (Trace m) m ()
resimulation_mh select = modifyM $ metropolis_hastings $ mix_mh select scaffold_resimulation_mh
