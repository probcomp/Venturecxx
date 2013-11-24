module SP where

import qualified Data.Map as M
import Control.Monad
import Control.Monad.Random -- From cabal install MonadRandom

import Language hiding (Value, Env)
import Trace

bernoulliFlip :: (MonadRandom m) => a -> b -> m Value
bernoulliFlip _ _ = liftM Boolean $ getRandomR (False,True)

bernoulli :: (MonadRandom m) => SP m
bernoulli = SP { requester = nullReq
               , log_d_req = Just $ trivial_log_d_req -- Only right for requests it actually made
               , outputter = bernoulliFlip
               , log_d_out = Just $ const $ const $ const $ -log 2.0
               }

-- Critical examples:
-- bernoulli
-- beta bernoulli in Venture
-- collapsed beta bernoulli
-- normal

-- Actually, need to initialize the env with a trace to allocate nodes and addresses
-- initialEnv :: Env
-- initialEnv = Frame (M.fromList [("bernoulli", bernoulli)]) Toplevel
