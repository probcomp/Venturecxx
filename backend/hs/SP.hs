{-# LANGUAGE FlexibleContexts #-}
module SP where

import qualified Data.Map as M
import Control.Monad.State.Lazy hiding (state)
import Control.Monad.State.Class
import Control.Monad.Random -- From cabal install MonadRandom
import Numeric.SpecFunctions -- From cabal install spec-functions

import Utils
import Language hiding (Value, Env, Exp)
import Trace hiding (SP(..), SPRequester(..), SPOutputter(..))
import qualified Trace as T
import Trace (SP)

-- Critical example SPs forcing aspects of the interface:
-- +                         just a basic deterministic function as an SP
-- bernoulli                 just a basic stochasitc function
-- normal                    a basic continuous stochastic function
-- compoundSP                Venture's lambda; forces selective absorbing
-- collapsed beta bernoulli  a higher-order SP, emitting SPs with state
-- mem                       exercises memoization of requests
-- make-hmm                  ?? forces latent simulation requests; anything else?
-- something                 forces AAA
-- others?

nullReq :: SPRequesterNS m
nullReq = DeterministicR $ \_ -> return []

trivial_log_d_req :: a -> b -> Double
trivial_log_d_req = const $ const $ 0.0

data NoStateSP m = NoStateSP
    { requester :: SPRequesterNS m
    , log_d_req :: Maybe ([Address] -> [SimulationRequest] -> Double)
    , outputter :: SPOutputterNS m
    , log_d_out :: Maybe ([Node] -> [Node] -> Value -> Double)
    }

data SPRequesterNS m = DeterministicR ([Address] -> UniqueSource [SimulationRequest])
                     | RandomR ([Address] -> UniqueSourceT m [SimulationRequest])

data SPOutputterNS m = Trivial
                     | DeterministicO ([Node] -> [Node] -> Value)
                     | RandomO ([Node] -> [Node] -> m Value)
                     | SPMaker ([Node] -> [Node] -> T.SP m) -- Are these ever random?

no_state_sp :: NoStateSP m -> T.SP m
no_state_sp NoStateSP { requester = req, log_d_req = ldr, outputter = out, log_d_out = ldo } =
    T.SP { T.requester = no_state_r req
         , T.log_d_req = liftM const ldr
         , T.outputter = no_state_o out
         , T.log_d_out = liftM const ldo
         , T.current = ()
         , T.incorporate = const id
         , T.unincorporate = const id
         }

no_state_r :: SPRequesterNS m -> T.SPRequester m a
no_state_r (DeterministicR f) = T.DeterministicR $ const f
no_state_r (RandomR f) = T.RandomR $ const f

no_state_o :: SPOutputterNS m -> T.SPOutputter m a
no_state_o Trivial = T.Trivial
no_state_o (DeterministicO f) = T.DeterministicO $ const f
no_state_o (RandomO f) = T.RandomO $ const f
no_state_o (SPMaker f) = T.SPMaker $ const f

compoundSP :: (Monad m) => [String] -> Exp -> Env -> SP m
compoundSP formals exp env = no_state_sp NoStateSP
  { requester = DeterministicR req
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
list = no_state_sp NoStateSP
  { requester = nullReq
  , log_d_req = Just $ trivial_log_d_req -- Only right for requests it actually made
  , outputter = DeterministicO execList
  , log_d_out = Nothing
  }

bernoulliFlip :: (MonadRandom m) => a -> b -> m Value
bernoulliFlip _ _ = liftM Boolean $ getRandomR (False,True)

bernoulli :: (MonadRandom m) => SP m
bernoulli = no_state_sp NoStateSP
  { requester = nullReq
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
weighted = no_state_sp NoStateSP
  { requester = nullReq
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
normal = no_state_sp NoStateSP
  { requester = nullReq
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
beta = no_state_sp NoStateSP
  { requester = nullReq
  , log_d_req = Just $ trivial_log_d_req -- Only right for requests it actually made
  , outputter = RandomO betaO
  , log_d_out = Just log_denisty_beta
  }

-- TODO abstract the actual coin flipping between collapsed beta bernoulli and weighted
cbeta_bernoulli_flip :: (MonadRandom m) => (Double,Double) -> [Node] -> [Node] -> m Value
cbeta_bernoulli_flip (ctYes, ctNo) [] [] = liftM Boolean $ liftM (< weight) $ getRandomR (0.0,1.0) where
    weight = ctYes / (ctYes + ctNo)
cbeta_bernoulli_flip _ _ _ = error "Incorrect arity for collapsed beta bernoulli"

cbeta_bernoulli_log_d :: (Double,Double) -> [Node] -> [Node] -> Value -> Double
cbeta_bernoulli_log_d (ctYes, ctNo) [] [] (Boolean True) = log weight where
    weight = ctYes / (ctYes + ctNo)
cbeta_bernoulli_log_d (ctYes, ctNo) [] [] (Boolean False) = log (1-weight) where
    weight = ctYes / (ctYes + ctNo)
cbeta_bernoulli_log_d _ [] [] _ = error "Value supplied to collapsed beta bernoulli log_d is not a boolean"
cbeta_bernoulli_log_d _ _ _ _ = error "Incorrect arity for collapsed beta bernoulli"

cbeta_bernoulli :: (MonadRandom m) => Double -> Double -> SP m
cbeta_bernoulli ctYes ctNo = no_state_sp NoStateSP
  { requester = nullReq
  , log_d_req = Just $ trivial_log_d_req -- Only right for requests it actually made
  , outputter = RandomO $ cbeta_bernoulli_flip (ctYes, ctNo)
  , log_d_out = Just $ cbeta_bernoulli_log_d (ctYes, ctNo)
  }

do_make_cbeta_bernoulli :: (MonadRandom m) => [Node] -> [Node] -> SP m
do_make_cbeta_bernoulli [yesN, noN] [] = cbeta_bernoulli yes no where
    yes = fromJust "Argument node had no value" $ (valueOf yesN >>= numberOf)
    no  = fromJust "Argument node had no value" $ (valueOf noN  >>= numberOf)
do_make_cbeta_bernoulli _ _ = error "Incorrect arity for make collapsed beta bernoulli"

make_cbeta_bernoulli :: (MonadRandom m) => SP m
make_cbeta_bernoulli = no_state_sp NoStateSP
  { requester = nullReq
  , log_d_req = Just $ trivial_log_d_req -- Only right for requests it actually made
  , outputter = SPMaker do_make_cbeta_bernoulli
  , log_d_out = Nothing
  }

selectO :: [Node] -> [Node] -> Value
selectO [p,c,a] _ = if fromJust "Argument node had no value" $ (valueOf p >>= booleanOf) then
                        fromJust "Argument node had no value" $ valueOf c
                    else
                        fromJust "Argument node had no value" $ valueOf a
selectO _ _ = error "Wrong number of arguments to SELECT"

select :: SP m
select = no_state_sp NoStateSP
  { requester = nullReq
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
                       , ("weighted", weighted)
                       , ("make-cbeta-bernoulli", make_cbeta_bernoulli)]
            names = map fst namedSps
            sps = map snd namedSps
