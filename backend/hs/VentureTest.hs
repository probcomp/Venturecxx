import System.Exit
import Test.HUnit

import qualified InterpretationTest

main :: IO ()
main = do
  Counts { failures = f, errors = e } <- runTestTT $ InterpretationTest.tests
  if f + e > 0 then
      exitWith $ ExitFailure $ f + e
  else
      exitSuccess
