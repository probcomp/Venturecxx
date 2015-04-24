{-# LANGUAGE DoAndIfThenElse #-}
{-# LANGUAGE ScopedTypeVariables #-}
{-# LANGUAGE ConstraintKinds #-}

module Inference where

import qualified Data.Set as S
import Control.Monad.Reader
import Control.Monad.Trans.State.Strict
import Control.Monad.Trans.Writer.Strict
import Control.Monad.Random hiding (randoms) -- From cabal install MonadRandom
import Control.Lens -- From cabal install lens

import Utils
import Language hiding (Exp, Value, Env)
import Trace
import Regen
import Detach
import qualified Subproblem as Sub

type MHAble m a num = a -> WriterT (LogDensity num) m a

data Assessable m a b num = Assessable (a -> m b) (a -> b -> LogDensity num)

metropolis_hastings :: (MonadRandom m, Real num) => MHAble m a num -> a -> m a
metropolis_hastings propose x = do
  (x', (LogDensity alpha)) <- runWriterT $ propose x
  (u :: Double) <- getRandomR (0.0,1.0)
  if (log u < realToFrac alpha) then
      return x'
  else
      return x

mix_mh :: (Monad m, Num num) =>
          (Assessable m a ind num) -> (ind -> MHAble m a num) -> (MHAble m a num)
mix_mh (Assessable sample measure) param_propose x = do
  ind <- lift $ sample x
  let ldRho = measure x ind
  tell $ log_density_negate ldRho
  x' <- param_propose ind x
  let ldXi = measure x' ind
  tell ldXi
  return x'

type Selector m num = Assessable m (Trace m num) Sub.Scaffold num

default_one :: (MonadRandom m, Floating num) => Selector m num
default_one = (Assessable sample log_density) where
    sample :: (MonadRandom m) => Trace m num -> m Sub.Scaffold
    sample trace =
        if trace^.randoms.to S.size == 0 then return $ Sub.empty []
        else do
          index <- getRandomR (0, trace^.randoms.to S.size - 1)
          let addr = (trace^.randoms.to S.toList) !! index
          let scaffold = runReader (Sub.scaffold_from_principal_nodes [addr]) trace
          return $ scaffold

    log_density :: (Floating num) => Trace m num -> Sub.Scaffold -> LogDensity num
    log_density t _ = LogDensity $ -log(fromIntegral $ t^.randoms.to S.size)

default_all :: (Monad m, Num num) => Selector m num
default_all = (Assessable sample log_density) where
    sample trace = return $ runReader (Sub.scaffold_from_principal_nodes (trace ^. randoms . to S.toList)) trace
    log_density _ _ = LogDensity 0

scaffold_resimulation_mh :: (MonadRandom m, Numerical num) =>
                            Sub.Scaffold -> MHAble m (Trace m num) num
scaffold_resimulation_mh scaffold trace = do
  torus <- censor log_density_negate $ returnT $ detach scaffold trace
  regen scaffold prior torus

resimulation_mh :: (MonadRandom m, Numerical num) => Selector m num -> StateT (Trace m num) m ()
resimulation_mh select = modifyM $ metropolis_hastings $ mix_mh select scaffold_resimulation_mh
