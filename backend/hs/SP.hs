{-# LANGUAGE FlexibleContexts #-}
module SP where

import qualified Data.Map as M
import Control.Monad.State.Lazy hiding (state)
import Control.Monad.Random -- From cabal install MonadRandom

import Utils
import Language hiding (Value, Env)
import Trace

bernoulliFlip :: (MonadRandom m) => a -> b -> m Value
bernoulliFlip _ _ = liftM Boolean $ getRandomR (False,True)

bernoulli :: (MonadRandom m) => SP m
bernoulli = SP { requester = nullReq
               , log_d_req = Just $ trivial_log_d_req -- Only right for requests it actually made
               , outputter = RandomO bernoulliFlip
               , log_d_out = Just $ const $ const $ const $ -log 2.0
               }

box_muller_cos :: Double -> Double -> Double
box_muller_cos u1 u2 = r * cos theta where
    r = sqrt (-2 * log u1)
    theta = 2 * pi * u2

normalFlip :: (MonadRandom m) => [Node] -> [Node] -> m Value
normalFlip [meanN, sigmaN] _ = do
  u1 <- getRandomR (0.0, 1.0)
  u2 <- getRandomR (0.0, 1.0)
  let normal = box_muller_cos u1 u2
      mu = fromJust "Argument node had no value" $ (valueOf meanN >>= numberOf)
      sigma = fromJust "Argument node had no value" $ (valueOf sigmaN >>= numberOf)
  return $ Number $ sigma * normal + mu

normal :: (MonadRandom m) => SP m
normal = SP { requester = nullReq
            , log_d_req = Just $ trivial_log_d_req -- Only right for requests it actually made
            , outputter = RandomO normalFlip
            , log_d_out = Nothing -- Just normalMeasure
            }

-- Critical examples:
-- bernoulli
-- beta bernoulli in Venture
-- collapsed beta bernoulli
-- normal

initializeBuiltins :: (MonadState (Trace m1) m, MonadRandom m1) => Env -> m Env
initializeBuiltins env = do
  spaddrs <- mapM (state . addFreshSP) sps
  addrs <- mapM (state . addFreshNode . Constant . Procedure) spaddrs
  return $ Frame (M.fromList $ zip names addrs) env
      where namedSps = [ ("bernoulli", bernoulli)
                       , ("normal", normal)]
            names = map fst namedSps
            sps = map snd namedSps
