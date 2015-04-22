import Control.Monad.State
import System.Environment (getArgs)

import Trace
import Venture
import qualified Inference as I

answer :: Int -> IO (Value Double)
answer steps = evalStateT (do
  assume "x" (app (var "normal") [0, 1])
  assume "y" $ app (var "normal") [var "x", 1]
  observe (var "y") 2
  replicateM_ steps (resimulation_mh I.default_one)
  sampleM (var "x")) initial

main :: IO ()
main = do [steps] <- liftM (fmap read) getArgs
          answer steps >>= (putStrLn . show)
