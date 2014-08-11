-- Statistical (unit) testing for Haskell.
-- Ported from Venturecxx/test/stats.py, which see for exposition.

module Statistical where

import qualified Data.Map as M
import Data.List

import Data.Random.Distribution
import Data.Random.Distribution.ChiSquare
import Math.Statistics.KSTest

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

chi2test :: [Int] -> [Double] -> (Double, PValue)
chi2test observed expected = (stat, pval) where
    stat = sum $ map cmp $ zip observed expected
    cmp (obs, exp) = (fromIntegral obs - exp) ** 2 / exp
    pval = sf (ChiSquare (fromIntegral (length expected) - 1)) stat

counts :: (Ord a, Eq a) => [a] -> [Int]
counts = map length . group . sort

normalize :: (Eq a, Ord a) => [(a, Double)] -> M.Map a Double
normalize items = M.fromList items' where
    total = sum $ map snd items
    items' = map scale items
    scale (i, rate) = (i, rate / total)

knownDiscrete :: (Ord a, Eq a) => [(a, Double)] -> [a] -> Result String
knownDiscrete expected_rates observed = Result (pval, msg) where
    total = length observed
    expected_cts = normalize expected_rates
    cts = map count $ M.keys expected_cts
    count item = length $ filter (== item) observed
    (chisq, pval) = chi2test cts $ map (* fromIntegral total) $ M.elems expected_cts
    msg = "discrete distribution didn't line up " ++ show chisq ++ " " ++ show pval -- TODO: more information

knownContinuous :: (CDF d t) => d t -> [t] -> Result String
knownContinuous distr observed = Result (pval, msg) where
    pval = ksTest (cdf distr) observed
    msg = "continuous distribution didn't line up " ++ show pval -- TODO: more information
