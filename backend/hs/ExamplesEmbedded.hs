module ExamplesEmbedded where

import Control.Monad
import Control.Monad.Random
import Control.Monad.Trans.State.Strict

import qualified Trace as T
import Venture
import qualified Inference as I
import Examples (v_if, v_let1)

flip_one_coin :: (MonadRandom m) => m (T.Value Double)
flip_one_coin = sample (T.app (T.var "bernoulli") []) initial

mh_flip_one_coin :: (MonadRandom m) => Int -> m (T.Value Double)
mh_flip_one_coin ct = evalStateT prog initial where
    -- prog :: (StateT (Model m) m) T.Value
    prog = do
      _ <- assume "c" $ T.app (T.var "bernoulli") []
      replicateM_ ct $ resimulation_mh I.default_one
      sampleM (T.var "c")

observed_chained_normals :: (MonadRandom m) => Int -> m (T.Value Double)
observed_chained_normals ct = evalStateT prog initial where
    prog = do
      _ <- assume "x" $ T.app (T.var "normal") [0, 2]
      _ <- assume "y" $ T.app (T.var "normal") [(T.var "x"), 2]
      observe (T.var "y") 4
      replicateM_ ct $ resimulation_mh I.default_one
      sampleM (T.var "x")
