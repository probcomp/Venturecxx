module GradientMethods where

import Control.Monad.Trans.Writer.Strict
import Data.Map (Map)
import System.IO.Unsafe (unsafePerformIO)
import System.Random

import Language (LogDensity(..))
import Trace
import Subproblem
import Regen

type Values num = Map Address (Value num)

new_random_source :: IO StdGen
new_random_source = getStdRandom split

with_random_source :: StdGen -> IO a -> IO a
with_random_source gen action = do
  old_gen <- getStdGen
  setStdGen gen
  result <- action
  setStdGen old_gen
  return result

derandomize :: StdGen -> IO a -> a
derandomize gen = unsafePerformIO . with_random_source gen

-- TODO Refactor the types in the rest of the program to allow the
-- fixed randomness phenomenon without having to resort to this
-- nonsense:
local_posterior :: (Real num1, Fractional num2) => Trace IO num1 -> Scaffold -> Values num2 -> LogDensity num2
local_posterior trace scaffold = unsafePerformIO (do
  gen <- new_random_source
  return (\values -> derandomize gen (do
    let proposal = prior `withDeterministic` values
    (_, logd) <- runWriterT $ Regen.regen scaffold proposal (realToFrac `fmap` trace)
    return logd)))
