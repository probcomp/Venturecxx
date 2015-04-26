{-# LANGUAGE OverloadedStrings #-}

import Control.Monad.State.Strict
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

answer2 :: Int -> IO (Value Double)
answer2 steps = evalStateT (do
  assume "coin" (app (var "make-cbeta-bernoulli") [1, 1])
  assume "result" (app (var "coin") [])
  replicateM_ steps (resimulation_mh I.default_one)
  sampleM (var "result")) initial

main :: IO ()
main = do [steps] <- liftM (fmap read) getArgs
          answer2 steps >>= (putStrLn . show)
