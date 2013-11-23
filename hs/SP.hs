module SP where

import Control.Monad
import Control.Monad.Random -- From cabal install MonadRandom

import Language hiding (Value)
import Trace

bernoulliFlip :: (MonadRandom m) => [Node] -> [Node] -> m Value
bernoulliFlip _ _ = liftM Boolean $ getRandomR (False,True)

bernoulli :: (MonadRandom m) => SP m
bernoulli = SP { requester = nullReq
               , log_d_req = Just $ trivial_log_d_req -- Only right for requests it actually made
               , outputter = bernoulliFlip
               , log_d_out = Just $ const $ const $ const $ -log 2.0
               }

