-- Statistical (unit) testing for Haskell.
-- Ported from Venturecxx/test/stats.py, which see for exposition.

module Statistical where

import Data.Random.Distribution
import Data.Random.Distribution.ChiSquare

type PValue = Double

newtype Result a = Result (PValue, a) -- Some displayable object

-- Survivor function.  Generally should be a separate method of the
-- CDF class, because it can be implemented numerically better
-- for situtations where the answer is close to 0.
sf :: CDF d t => d t -> t -> Double
sf d x = 1 - cdf d x

fisherMethod :: [PValue] -> PValue
fisherMethod pvals | any (== 0) pvals = 0
                   | otherwise = sf (ChiSquare (2 * fromIntegral (length pvals))) chisq where
                   chisq = -2 * (sum $ map log pvals)
