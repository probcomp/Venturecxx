{-# LANGUAGE FlexibleContexts #-}
module SP where

import qualified Data.Map as M
import Control.Monad.State.Lazy hiding (state)
import Control.Monad.State.Class
import Control.Monad.Random -- From cabal install MonadRandom
import Numeric.SpecFunctions -- From cabal install spec-functions

import Utils
import Language hiding (Value, Env, Exp)
import Trace

-- Critical example SPs forcing aspects of the interface:
-- +                         just a basic deterministic function as an SP
-- bernoulli                 just a basic stochasitc function
-- normal                    a basic continuous stochastic function
-- compoundSP                Venture's lambda; forces selective absorbing
-- collapsed beta bernoulli  a higher-order SP with state
-- mem                       exercises memoization of requests
-- make-hmm                  ?? forces latent simulation requests; anything else?
-- something                 forces AAA
-- others?

nullReq :: SPRequester m
nullReq = DeterministicR $ \_ -> return []

trivial_log_d_req :: a -> b -> Double
trivial_log_d_req = const $ const $ 0.0

compoundSP :: (Monad m) => [String] -> Exp -> Env -> SP m
compoundSP formals exp env =
    SP { requester = DeterministicR req
       , log_d_req = Just $ trivial_log_d_req
       , outputter = Trivial
       , log_d_out = Nothing -- Or Just (0 if it's right, -inf if not?)
       } where
        req args = do
          freshId <- liftM SRId fresh
          let r = SimulationRequest freshId exp $ Frame (M.fromList $ zip formals args) env
          return [r]

execList :: [Node] -> [Node] -> Value
execList ns [] = List $ map (fromJust "Argument node had no value" . valueOf) ns
execList _ _ = error "List SP given fulfilments"

list :: (Monad m) => SP m
list = SP { requester = nullReq
          , log_d_req = Just $ trivial_log_d_req -- Only right for requests it actually made
          , outputter = DeterministicO execList
          , log_d_out = Nothing
          }

bernoulliFlip :: (MonadRandom m) => a -> b -> m Value
bernoulliFlip _ _ = liftM Boolean $ getRandomR (False,True)

bernoulli :: (MonadRandom m) => SP m
bernoulli = SP { requester = nullReq
               , log_d_req = Just $ trivial_log_d_req -- Only right for requests it actually made
               , outputter = RandomO bernoulliFlip
               , log_d_out = Just $ const $ const $ const $ -log 2.0
               }

weightedFlip :: (MonadRandom m) => [Node] -> b -> m Value
weightedFlip [wt] _ = liftM Boolean $ liftM (< weight) $ getRandomR (0.0,1.0) where
    weight = fromJust "No number supplied for weighted" $ (valueOf wt >>= numberOf)
weightedFlip _ _ = error "Wrong number of arguments to weight"

log_d_weight :: [Node] -> b -> Value -> Double
log_d_weight [wt] _ (Boolean True) = log weight where
    weight = fromJust "No number supplied for weighted" $ (valueOf wt >>= numberOf)
log_d_weight [wt] _ (Boolean False) = log (1 - weight) where
    weight = fromJust "No number supplied for weighted" $ (valueOf wt >>= numberOf)
log_d_weight [_] _ _ = error "Value supplied to log_d_weight is not a boolean"
log_d_weight _ _ _ = error "Incorrect number of arguments to log_d_weight"

weighted :: (MonadRandom m) => SP m
weighted = SP { requester = nullReq
               , log_d_req = Just $ trivial_log_d_req -- Only right for requests it actually made
               , outputter = RandomO weightedFlip
               , log_d_out = Just log_d_weight
               }

box_muller_cos :: Double -> Double -> Double
box_muller_cos u1 u2 = r * cos theta where
    r = sqrt (-2 * log u1)
    theta = 2 * pi * u2

normalFlip :: (MonadRandom m) => [Node] -> [Node] -> m Value
normalFlip [meanN, sigmaN] [] = do
  u1 <- getRandomR (0.0, 1.0)
  u2 <- getRandomR (0.0, 1.0)
  let normal = box_muller_cos u1 u2
      mu = fromJust "Argument node had no value" $ (valueOf meanN >>= numberOf)
      sigma = fromJust "Argument node had no value" $ (valueOf sigmaN >>= numberOf)
  return $ Number $ sigma * normal + mu
normalFlip _ _ = error "Incorrect arity for normal"

log_d_normal' :: Double -> Double -> Double -> Double
log_d_normal' mean sigma x = - (x - mean)^^2 / (2 * sigma ^^ 2) - scale where
    scale = log sigma + (log pi)/2

log_d_normal :: [Node] -> [Node] -> Value -> Double
log_d_normal args@[_,_] [] (Number x) = log_d_normal' mu sigma x where
    [mu, sigma] = map (fromJust "Argument node had no value" . (\n -> valueOf n >>= numberOf)) args
log_d_normal [_,_] [] _ = error "Given Value must be a number"
log_d_normal _ _ _ = error "Incorrect arity for log_d_normal"

normal :: (MonadRandom m) => SP m
normal = SP { requester = nullReq
            , log_d_req = Just $ trivial_log_d_req -- Only right for requests it actually made
            , outputter = RandomO normalFlip
            , log_d_out = Just log_d_normal
            }

betaO :: (MonadRandom m) => [Node] -> [b] -> m Value
betaO [alphaN, betaN] [] = do
  -- Adapted from Statistics.Distribution.Beta; not reused because of
  -- funny randomness management convention.
  x <- getRandomR (0.0,1.0)
  return $ Number $ quantile x
    where
      alpha = fromJust "Argument node had no value" $ (valueOf alphaN >>= numberOf)
      beta = fromJust "Argument node had no value" $ (valueOf betaN >>= numberOf)
      quantile x | x == 0 = 0
                 | x == 1 = 1
                 | 0 < x && x < 1 = invIncompleteBeta alpha beta x
                 | otherwise = error $ "x must be in the range [0,1], got: " ++ show x
betaO _ _ = error "Incorrect arity for beta"

log_denisty_beta :: [Node] -> [b] -> Value -> Double
log_denisty_beta [alphaN, betaN] [] (Number x) = (a-1)*log x + (b-1)*log (1-x) - logBeta a b where
    a = fromJust "Argument node had no value" $ (valueOf alphaN >>= numberOf)
    b = fromJust "Argument node had no value" $ (valueOf betaN >>= numberOf)
log_denisty_beta [_,_] [] _ = error "Given Value must be a number"
log_denisty_beta _ _ _ = error "Incorrect arity for log_density_beta"

beta :: (MonadRandom m) => SP m
beta = SP { requester = nullReq
          , log_d_req = Just $ trivial_log_d_req -- Only right for requests it actually made
          , outputter = RandomO betaO
          , log_d_out = Just log_denisty_beta
          }

selectO :: [Node] -> [Node] -> Value
selectO [p,c,a] _ = if fromJust "Argument node had no value" $ (valueOf p >>= booleanOf) then
                        fromJust "Argument node had no value" $ valueOf c
                    else
                        fromJust "Argument node had no value" $ valueOf a
selectO _ _ = error "Wrong number of arguments to SELECT"

select :: SP m
select = SP { requester = nullReq
            , log_d_req = Just $ trivial_log_d_req
            , outputter = DeterministicO selectO
            , log_d_out = Nothing -- Or Just (0 if it's right, -inf if not?)
            }

initializeBuiltins :: (MonadState (Trace m1) m, MonadRandom m1) => Env -> m Env
initializeBuiltins env = do
  spaddrs <- mapM (state . addFreshSP) sps
  addrs <- mapM (state . addFreshNode . Constant . Procedure) spaddrs
  return $ Frame (M.fromList $ zip names addrs) env
      where namedSps = [ ("bernoulli", bernoulli)
                       , ("normal", normal)
                       , ("beta", beta)
                       , ("select", select)
                       , ("list", list)
                       , ("weighted", weighted)]
            names = map fst namedSps
            sps = map snd namedSps
