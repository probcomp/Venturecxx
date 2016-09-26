{-# LANGUAGE ScopedTypeVariables #-}

module Distributions where

import Control.Monad
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
log_d_uniform_c low high x | low <= x && x <= high = - (log (high - low))
                           | otherwise = log 0

-- TODO A type for integers?
uniform_d_flip :: forall m num. (MonadRandom m, RealFrac num) => num -> num -> m num
uniform_d_flip low high = do
  res <- (getRandomR (ceiling low, floor high)) :: m Int
  return $ fromIntegral res

-- TODO Uniform-discrete's log density should have no derivatives
log_d_uniform_d :: (Ord num, Floating num) => num -> num -> num -> num
log_d_uniform_d low high x | low <= x && x <= high = - (log (high - low))
                           | otherwise = log 0

---- Categorical

-- Adapted from MonadRandom.fromList.  Who thought it could possibly
-- be a good idea to restrict the weight type to Rational of all
-- things?  Especially since that one did its arithmetic in floating
-- point?
simulate_categorical :: (MonadRandom m, Ord num, Num num, Random num) => [(a,num)] -> m a
simulate_categorical [] = error "simulate_categorical called with empty list"
simulate_categorical [(x,_)] = return x
simulate_categorical xs = do
  -- TODO: Better error message if weights sum to 0.
  let s = (sum (map snd xs))
      cs = scanl1 (\(_,q) (y,s') -> (y, s'+q)) xs       -- cumulative weight
  p <- getRandomR (0,s)
  return . fst . head $ dropWhile (\(_,q) -> q < p) cs

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

xxxFakeGenericity  :: (Real num, Fractional num) => (Double -> Double) -> (num -> num)
xxxFakeGenericity  f x1 = realToFrac $ f (realToFrac x1)

xxxFakeGenericity2 :: (Real num, Fractional num) =>
                      (Double -> Double -> Double) -> (num -> num -> num)
xxxFakeGenericity2 f x1 x2 = realToFrac $ f (realToFrac x1) (realToFrac x2)

xxxFakeGenericity2M :: (Monad m, Real num, Fractional num) =>
                       (Double -> Double -> m Double) -> (num -> num -> m num)
xxxFakeGenericity2M f x1 x2 = liftM realToFrac $ f (realToFrac x1) (realToFrac x2)

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

log_d_beta :: (Floating num, Real num) => num -> num -> num -> num
log_d_beta a b x = (a-1)*log x + (b-1)*log (1-x) - xxxFakeGenericity2 logBeta a b

---- Gamma

-- Grump again.  I seem to be again losing from people imposing
-- incompatible interfaces on their code.  I want

gammaDouble :: forall m. (MonadRandom m) => Double -> Double -> m Double

-- I wish I could reuse, e.g., Data.Random.Distribution.Gamma.gamma with
--   gamma shape scale = ??? $ Gamma.gamma shape scale
-- but in order to do that, I would need to write a combinator of type
--   ??? :: (MonadRandom m) => RVar a -> m a
-- that could sample from an arbitrary RVar in an arbitrary instance
-- of the MonadRandom package's MonadRandom.  This is clearly
-- nonsense.  So I copy and modify code to have the interface I want.

-- In this case, since I'm copying anyway, I decided to copy from
-- System.Random.MWC.Distributions.gamma

{-# INLINE gammaDouble #-}
gammaDouble a b
  | a <= 0    = error "negative shape parameter for gamma distribution"
  | otherwise = mainloop
    where
      mainloop = do
        T x v <- innerloop
        u     <- getRandomR (0.0, 1.0)
        let cont =  u > 1 - 0.331 * sqr (sqr x)
                 && log u > 0.5 * sqr x + a1 * (1 - v + log v) -- Rarely evaluated
        case () of
          _| cont      -> mainloop
           | a >= 1    -> return $! a1 * v * b
           | otherwise -> do y <- getRandomR (0.0, 1.0)
                             return $! y ** (1 / a) * a1 * v * b
      -- inner loop
      innerloop = do
        x <- normal_flip 0 1
        case 1 + a2*x of
          v | v <= 0    -> innerloop
            | otherwise -> return $! T x (v*v*v)
      -- constants
      a' = if a < 1 then a + 1 else a
      a1 = a' - 1/3
      a2 = 1 / sqrt(9 * a1)
      sqr x = x * x

-- Unboxed 2-tuple
data T = T {-# UNPACK #-} !Double {-# UNPACK #-} !Double

gamma :: (MonadRandom m, Real num, Fractional num) => num -> num -> m num
gamma = xxxFakeGenericity2M gammaDouble

log_d_gamma :: (Real num, Floating num) => num -> num -> num -> num
log_d_gamma shape scale x = c + (shape - 1) * x + (-x / scale) where
  c = -(shape * log scale + (xxxFakeGenericity logGamma) shape)

inv_gamma :: (MonadRandom m, Real num, Fractional num) => num -> num -> m num
inv_gamma shape scale = liftM (\x -> 1/x) $ gamma shape scale

log_d_inv_gamma :: (Real num, Floating num) => num -> num -> num -> num
log_d_inv_gamma shape scale x = c + (-shape - 1) * x + (-scale / x) where
  c = shape * log scale - (xxxFakeGenericity logGamma) shape
