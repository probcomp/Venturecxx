module GradientTest where

import Control.Lens  -- from cabal install lens
import Control.Monad
import Control.Monad.Trans.State.Lazy
import Data.Functor.Compose
import qualified Data.Map as Map
import Numeric.AD.Mode.Reverse (grad)

import qualified Language as L
import qualified Trace
import Subproblem
import Venture
import Inference
import GradientMethods
    
test_grad :: IO (Values Double, Values Double)
test_grad = evalStateT prog initial where
  prog = do
    _ <- assume "x" $ Trace.app (Trace.var "normal") [0, 1]
    scaffold <- select default_all
    m <- get
    let current = principal_values scaffold m
    _ <- detach scaffold
    t <- use trace
    return (getCompose $ grad (unlog . (local_posterior t scaffold) . getCompose) (Compose current), current)
  unlog (L.LogDensity x) = x

principal_values :: Scaffold -> Model m num -> Map.Map Trace.Address (Trace.Value num)
principal_values scaffold model = Map.fromList $ zip as $ map (flip lookupValue model) as where
    as = _principal scaffold

main :: IO ()
main = liftM show test_grad >>= putStrLn
