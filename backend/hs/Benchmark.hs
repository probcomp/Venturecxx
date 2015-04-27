{-# LANGUAGE OverloadedStrings #-}

import Control.Monad.State.Strict
import System.Environment (getArgs)

import Utils (Pretty(..))
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
  mapM_ infer [0..steps-1]
  sampleM (var "result")) initial
    where infer step = do resimulation_mh I.default_one
                          if step `mod` 499 == 0 then do
                              model <- gets _trace
                              lift $ putStrLn $ show $ pp model
                          else
                              return ()

answer3 :: Int -> IO [(Value Double)]
answer3 steps = mapM (\_ -> answer2 $ steps `div` 10) [1..10]

main :: IO ()
main = do [index, steps] <- liftM (fmap read) getArgs
          let act = [ answer steps >>= (putStrLn . show)
                    , answer2 steps >>= (putStrLn . show)
                    , answer3 steps >>= (putStrLn . show)] !! index
          act
