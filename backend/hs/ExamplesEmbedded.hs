module ExamplesEmbedded where

import Control.Monad
import Control.Monad.Random
import Control.Monad.Trans.State.Lazy

import qualified Language as L
import qualified Trace as T
import Venture
import qualified Inference as I
import Examples (v_if, v_let1)

flip_one_coin :: (MonadRandom m) => m (T.Value Double)
flip_one_coin = sample (L.App (L.Var "bernoulli") []) initial

mh_flip_one_coin :: (MonadRandom m) => Int -> m (T.Value Double)
mh_flip_one_coin ct = evalStateT prog initial where
    -- prog :: (StateT (Model m) m) T.Value
    prog = do
      _ <- assume "c" $ L.App (L.Var "bernoulli") []
      replicateM_ ct $ resimulation_mh I.default_one
      sampleM (L.Var "c")

observed_chained_normals :: (MonadRandom m) => Int -> m (T.Value Double)
observed_chained_normals ct = evalStateT prog initial where
    prog = do
      _ <- assume "x" $ L.App (L.Var "normal") [0, 2]
      _ <- assume "y" $ L.App (L.Var "normal") [(L.Var "x"), 2]
      observe (L.Var "y") 4
      replicateM_ ct $ resimulation_mh I.default_one
      sampleM (L.Var "x")
