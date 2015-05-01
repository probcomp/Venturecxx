{-# LANGUAGE ScopedTypeVariables #-}

module Distributions where

import Control.Monad.Random
import Numeric.SpecFunctions -- From cabal install spec-functions

---- Bernoulli trials

weighted_flip :: (MonadRandom m, Real num) => num -> m Bool
weighted_flip weight = do
  (toss :: Double) <- getRandomR (0.0,1.0)
  return $ toss < realToFrac weight

log_d_weight :: (Floating num) => num -> Bool -> num
log_d_weight weight True = log weight
log_d_weight weight False = log (1 - weight)

---- Uniform distributions

uniform_c_flip :: forall m num. (MonadRandom m, Fractional num) => num -> num -> m num
uniform_c_flip low high = do
  unit <- (getRandomR (0.0, 1.0)) :: m Double
  return $ low + (realToFrac unit) * (high - low)

log_d_uniform_c :: (Ord num, Floating num) => num -> num -> num -> num
log_d_uniform_c x low high | low <= x && x <= high = - (log (high - low))
                           | otherwise = log 0

-- TODO A type for integers?
uniform_d_flip :: forall m num. (MonadRandom m, RealFrac num) => num -> num -> m num
uniform_d_flip low high = do
  res <- (getRandomR (ceiling low, floor high)) :: m Int
  return $ fromIntegral res

-- TODO Uniform-discrete's log density should have no derivatives
log_d_uniform_d :: (Ord num, Floating num) => num -> num -> num -> num
log_d_uniform_d x low high | low <= x && x <= high = - (log (high - low))
                           | otherwise = log 0

---- Normal

box_muller_cos :: Double -> Double -> Double
box_muller_cos u1 u2 = r * cos theta where
    r = sqrt (-2 * log u1)
    theta = 2 * pi * u2

normal_flip :: (MonadRandom m, Fractional num) => num -> num -> m num
normal_flip mu sigma = do
  u1 <- getRandomR (0.0, 1.0)
  u2 <- getRandomR (0.0, 1.0)
  let normal = box_muller_cos u1 u2
  return $ sigma * realToFrac normal + mu

log_d_normal :: (Floating num) => num -> num -> num -> num
log_d_normal mean sigma x = - (x - mean)^^(2::Int) / (2 * sigma^^(2::Int)) - scale where
    scale = log sigma + (log pi)/2

----- Beta

xxxFakeGenericity2 :: (Real num, Fractional num) =>
                      (Double -> Double -> Double) -> (num -> num -> num)
xxxFakeGenericity2 f x1 x2 = realToFrac $ f (realToFrac x1) (realToFrac x2)

xxxFakeGenericity3 :: (Real num, Fractional num) =>
                      (Double -> Double -> Double -> Double) -> (num -> num -> Double -> num)
xxxFakeGenericity3 f x1 x2 x3 = realToFrac $ f (realToFrac x1) (realToFrac x2) x3

beta :: forall m num. (MonadRandom m, Real num, Fractional num) => num -> num -> m num
beta alpha beta = do
  -- Adapted from Statistics.Distribution.Beta; not reused because of
  -- funny randomness management convention.
  x <- getRandomR (0.0,1.0)
  return $ quantile x
    where
      quantile :: Double -> num
      quantile x | x == 0 = 0
                 | x == 1 = 1
                 | 0 < x && x < 1 = xxxFakeGenericity3 invIncompleteBeta alpha beta x
                 | otherwise = error $ "x must be in the range [0,1], got: " ++ show x

log_denisty_beta :: (Floating num, Real num) => num -> num -> num -> num
log_denisty_beta a b x = (a-1)*log x + (b-1)*log (1-x) - xxxFakeGenericity2 logBeta a b
