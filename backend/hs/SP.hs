{-# LANGUAGE FlexibleContexts #-}
module SP where

import qualified Data.Map as M
import Control.Monad.State.Lazy hiding (state)
import Control.Monad.State.Class
import Control.Monad.Random -- From cabal install MonadRandom
import Numeric.SpecFunctions -- From cabal install spec-functions
import Control.Lens  -- from cabal install lens

import Utils
import Language hiding (Value, Env, Exp)
import Trace hiding (SP(..), SPRequester(..), SPOutputter(..))
import qualified Trace as T
import Trace (SP)

-- Critical example SPs forcing aspects of the interface:
-- +                         just a basic deterministic function as an SP
-- bernoulli                 just a basic stochastic function
-- normal                    a basic continuous stochastic function
-- compoundSP                Venture's lambda; forces selective absorbing
-- collapsed beta bernoulli  a higher-order SP, emitting SPs with state
-- mem                       exercises memoization of requests
-- make-hmm                  ?? forces latent simulation requests; anything else?
-- collapsed beta bernoulli  forces AAA under proposing to the hyperparameters
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

on_values :: ([Value] -> [Value] -> a) -> ([Node] -> [Node] -> a)
on_values f ns1 ns2 = f vs1 vs2 where
    vs1 = map (fromJust "Argument node had no value" . valueOf) ns1
    vs2 = map (fromJust "Fulfilment node had no value" . valueOf) ns2

-- TODO Is there a clean way to pass down the name of the procedure
-- here, so it can be included in the error message?
binary :: (a -> a -> r) -> [a] -> [b] -> r
binary f [a1,a2] [] = f a1 a2
binary _ [_,_] l = error $ "No requests expected " ++ (show $ length l) ++ " given."
binary _ l _ = error $ "Two arguments expected " ++ (show $ length l) ++ " given."

unary :: (a -> r) -> [a] -> [b] -> r
unary f [a] [] = f a
unary _ [_] l = error $ "No requests expected " ++ (show $ length l) ++ " given."
unary _ l _ = error $ "One argument expected " ++ (show $ length l) ++ " given."

nullary :: r -> [a] -> [b] -> r
nullary f [] [] = f
nullary _ [] l = error $ "No requests expected " ++ (show $ length l) ++ " given."
nullary _ l _ = error $ "No arguments expected " ++ (show $ length l) ++ " given."

-- Is there a better name for these three combinators?
typed :: (Valuable a) => (a -> r) -> Value -> r
typed f = f . (fromJust "Incorrect type argument") . fromValue

typed2 :: (Valuable a, Valuable b) => (a -> b -> r) -> Value -> Value -> r
typed2 = typed . (typed .)

typed3 :: (Valuable a, Valuable b, Valuable c) => (a -> b -> c -> r) -> Value -> Value -> Value -> r
typed3 = typed . (typed2 .)

execList :: [Value] -> [b] -> Value
execList vs [] = List vs
execList _ _ = error "List SP given fulfilments"

list :: (Monad m) => SP m
list = no_state_sp NoStateSP
  { requester = nullReq
  , log_d_req = Just $ trivial_log_d_req -- Only right for requests it actually made
  , outputter = DeterministicO $ on_values execList
  , log_d_out = Nothing
  }

bernoulliFlip :: (MonadRandom m) => m Value
bernoulliFlip = liftM Boolean $ getRandomR (False,True)

bernoulli :: (MonadRandom m) => SP m
bernoulli = no_state_sp NoStateSP
  { requester = nullReq
  , log_d_req = Just $ trivial_log_d_req -- Only right for requests it actually made
  , outputter = RandomO $ nullary bernoulliFlip
  , log_d_out = Just $ nullary $ const $ -log 2.0
  }

weightedFlip :: (MonadRandom m) => Value -> m Value
weightedFlip wt = liftM Boolean $ liftM (< weight) $ getRandomR (0.0,1.0) where
    weight = fromJust "No number supplied for weighted" $ numberOf wt

log_d_weight :: Value -> Value -> Double
log_d_weight wt (Boolean True) = log weight where
    weight = fromJust "No number supplied for weighted" $ numberOf wt
log_d_weight wt (Boolean False) = log (1 - weight) where
    weight = fromJust "No number supplied for weighted" $ numberOf wt
log_d_weight _ _ = error "Value supplied to log_d_weight is not a boolean"

weighted :: (MonadRandom m) => SP m
weighted = no_state_sp NoStateSP
  { requester = nullReq
  , log_d_req = Just $ trivial_log_d_req -- Only right for requests it actually made
  , outputter = RandomO $ on_values $ unary weightedFlip
  , log_d_out = Just $ on_values $ unary log_d_weight
  }

box_muller_cos :: Double -> Double -> Double
box_muller_cos u1 u2 = r * cos theta where
    r = sqrt (-2 * log u1)
    theta = 2 * pi * u2

normalFlip :: (MonadRandom m) => Value -> Value -> m Value
normalFlip meanV sigmaV = do
  u1 <- getRandomR (0.0, 1.0)
  u2 <- getRandomR (0.0, 1.0)
  let normal = box_muller_cos u1 u2
      mu = fromJust "Argument value was not a number" $ numberOf meanV
      sigma = fromJust "Argument value was not a number" $ numberOf sigmaV
  return $ Number $ sigma * normal + mu

log_d_normal' :: Double -> Double -> Double -> Double
log_d_normal' mean sigma x = - (x - mean)^^2 / (2 * sigma ^^ 2) - scale where
    scale = log sigma + (log pi)/2

log_d_normal :: Value -> Value -> Value -> Double
log_d_normal muV sigmaV (Number x) = log_d_normal' mu sigma x where
    [mu, sigma] = map (fromJust "Argument value was not a number" . numberOf) [muV, sigmaV]
log_d_normal _ _ _ = error "Given Value must be a number"

normal :: (MonadRandom m) => SP m
normal = no_state_sp NoStateSP
  { requester = nullReq
  , log_d_req = Just $ trivial_log_d_req -- Only right for requests it actually made
  , outputter = RandomO $ on_values $ binary normalFlip
  , log_d_out = Just $ on_values $ binary log_d_normal
  }

betaO :: (MonadRandom m) => Value -> Value -> m Value
betaO alphaV betaV = do
  -- Adapted from Statistics.Distribution.Beta; not reused because of
  -- funny randomness management convention.
  x <- getRandomR (0.0,1.0)
  return $ Number $ quantile x
    where
      alpha = fromJust "Argument value was not a number" $ numberOf alphaV
      beta = fromJust "Argument value was not a number" $ numberOf betaV
      quantile x | x == 0 = 0
                 | x == 1 = 1
                 | 0 < x && x < 1 = invIncompleteBeta alpha beta x
                 | otherwise = error $ "x must be in the range [0,1], got: " ++ show x

log_denisty_beta :: Value -> Value -> Value -> Double
log_denisty_beta alphaV betaV (Number x) = (a-1)*log x + (b-1)*log (1-x) - logBeta a b where
    a = fromJust "Argument value was not a number" $ numberOf alphaV
    b = fromJust "Argument value was not a number" $ numberOf betaV
log_denisty_beta _ _ _ = error "Given Value must be a number"

beta :: (MonadRandom m) => SP m
beta = no_state_sp NoStateSP
  { requester = nullReq
  , log_d_req = Just $ trivial_log_d_req -- Only right for requests it actually made
  , outputter = RandomO $ on_values $ binary betaO
  , log_d_out = Just $ on_values $ binary log_denisty_beta
  }

-- TODO abstract the actual coin flipping between collapsed beta bernoulli and weighted
cbeta_bernoulli_flip :: (MonadRandom m) => (Double,Double) -> m Value
cbeta_bernoulli_flip (ctYes, ctNo) = liftM Boolean $ liftM (< weight) $ getRandomR (0.0,1.0) where
    weight = ctYes / (ctYes + ctNo)

cbeta_bernoulli_log_d :: (Double,Double) -> Value -> Double
cbeta_bernoulli_log_d (ctYes, ctNo) (Boolean True) = log weight where
    weight = ctYes / (ctYes + ctNo)
cbeta_bernoulli_log_d (ctYes, ctNo) (Boolean False) = log (1-weight) where
    weight = ctYes / (ctYes + ctNo)
cbeta_bernoulli_log_d _ _ = error "Value supplied to collapsed beta bernoulli log_d is not a boolean"

cbeta_bernoulli_frob :: (Double -> Double) -> Value -> (Double,Double) -> (Double,Double)
cbeta_bernoulli_frob f (Boolean True)  s = s & _1 %~ f
cbeta_bernoulli_frob f (Boolean False) s = s & _2 %~ f
cbeta_bernoulli_frob _ _ _ = error "Trying to incorporate a non-boolean into collapsed beta bernoulli"

cbeta_bernoulli :: (MonadRandom m) => Double -> Double -> SP m
cbeta_bernoulli ctYes ctNo = T.SP
  { T.requester = no_state_r nullReq
  , T.log_d_req = Just $ const trivial_log_d_req -- Only right for requests it actually made
  , T.outputter = T.RandomO $ nullary . cbeta_bernoulli_flip
  , T.log_d_out = Just $ nullary . cbeta_bernoulli_log_d
  , T.current = (ctYes, ctNo)
  , T.incorporate = cbeta_bernoulli_frob succ
  , T.unincorporate = cbeta_bernoulli_frob pred
  }

do_make_cbeta_bernoulli :: (MonadRandom m) => Value -> Value -> SP m
do_make_cbeta_bernoulli yesV noV = cbeta_bernoulli yes no where
    yes = fromJust "Argument value was not a number" $ numberOf yesV
    no  = fromJust "Argument value was not a number" $ numberOf noV

make_cbeta_bernoulli :: (MonadRandom m) => SP m
make_cbeta_bernoulli = no_state_sp NoStateSP
  { requester = nullReq
  , log_d_req = Just $ trivial_log_d_req -- Only right for requests it actually made
  , outputter = SPMaker $ on_values $ binary do_make_cbeta_bernoulli
  , log_d_out = Nothing
  }

selectO :: [Value] -> [b] -> Value
selectO [p,c,a] [] = if fromJust "Predicate was not a boolean" $ booleanOf p then c
                     else a
selectO _ _ = error "Wrong number of arguments to SELECT"

select :: SP m
select = no_state_sp NoStateSP
  { requester = nullReq
  , log_d_req = Just $ trivial_log_d_req
  , outputter = DeterministicO $ on_values selectO
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
