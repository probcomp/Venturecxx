{-# LANGUAGE OverloadedStrings #-}
{-# LANGUAGE FlexibleContexts #-}
{-# LANGUAGE ScopedTypeVariables #-}
{-# LANGUAGE RankNTypes #-}
{-# LANGUAGE ConstraintKinds #-}

module SP where

import Data.Functor.Compose
import qualified Data.Map.Strict as M
import qualified Data.Maybe.Strict as Strict
import Data.List (foldl')
import qualified Data.Text as DT
import Data.Tuple.Strict (Pair(..))
import Control.Monad.State.Strict hiding (state)
import Control.Monad.State.Class
import Control.Monad.Reader
import Control.Monad.Random -- From cabal install MonadRandom
import Numeric.SpecFunctions -- From cabal install spec-functions
import Control.Lens  -- from cabal install lens
import qualified Data.Vector as V

import Utils
import Distributions
import Language hiding (Value, Env, Exp)
import Trace hiding (SP(..), SPRequester(..), SPOutputter(..))
import qualified Trace as T
import Trace (SP)

-- Critical example SPs forcing aspects of the interface:
-- +                         just a basic deterministic function as an SP
-- bernoulli                 just a basic stochastic function
-- normal                    a basic continuous stochastic function; absorbing forces log densities
-- select                    one way to do if; forces a brush
-- compoundSP                Venture's lambda; forces ESRs and selective absorbing
-- observe (not an SP)       forces constraints and propagation thereof
-- collapsed beta bernoulli  a higher-order SP, emitting SPs with state
-- mem                       exercises memoization of requests
-- collapsed beta bernoulli  forces AAA under proposing to the hyperparameters
-- make-lazy-hmm             forces latent simulation requests; advanced version forces AEKernels

nullReq :: SPRequesterNS m
nullReq = DeterministicR $ \_ -> return []

trivial_log_d_req :: (Num num) => a -> b -> num
trivial_log_d_req = const $ const $ 0

newtype LogDReqNS =
    LogDReqNS (forall num. (T.Numerical num) => [Address] -> [SimulationRequest num] -> num)
newtype LogDOutNS =
    LogDOutNS (forall num. (T.Numerical num) => [Node num] -> [Node num] -> Value num -> num)

data NoStateSP m = NoStateSP
    { requester :: !(SPRequesterNS m)
    , log_d_req :: !(Strict.Maybe LogDReqNS)
    , outputter :: !(SPOutputterNS m)
    , log_d_out :: !(Strict.Maybe LogDOutNS)
    }

data SPRequesterNS m
    = DeterministicR !(forall num. (T.Numerical num) => [Address] -> UniqueSource [SimulationRequest num])
    | RandomR !(forall num. [Address] -> UniqueSourceT m [SimulationRequest num])
    | ReaderR !(forall num. [Address] -> ReaderT (Trace m num) UniqueSource [SimulationRequest num])

data SPOutputterNS m
    = Trivial
    | DeterministicO !(forall num. (T.Numerical num) => [Node num] -> [Node num] -> Value num)
    | RandomO !(forall num. (T.Numerical num) => [Node num] -> [Node num] -> m (Value num))
    | SPMaker !(forall num. (T.Numerical num) => [Node num] -> [Node num] -> SP m) -- Are these ever random?
    | ReferringSPMaker !([Address] -> [Address] -> SP m)

no_state_sp :: NoStateSP m -> SP m
no_state_sp NoStateSP { requester = req, log_d_req = ldr, outputter = out, log_d_out = ldo } =
    T.SP { T.requester = no_state_r req
         , T.log_d_req = fmap convert1 ldr
         , T.outputter = no_state_o out
         , T.log_d_out = fmap convert2 ldo
         , T.current = ()
         , T.incorporate = const id
         , T.unincorporate = const id
         , T.incorporateR = const $ const id
         , T.unincorporateR = const $ const id
         } where
        convert1 (LogDReqNS f) = T.LogDReq $ const f
        convert2 (LogDOutNS f) = T.LogDOut $ const f

no_state_r :: SPRequesterNS m -> T.SPRequester m a
no_state_r (DeterministicR f) = T.DeterministicR $ const f
no_state_r (RandomR f) = T.RandomR $ const f
no_state_r (ReaderR f) = T.ReaderR $ const f

no_state_o :: SPOutputterNS m -> T.SPOutputter m a
no_state_o Trivial = T.Trivial
no_state_o (DeterministicO f) = T.DeterministicO $ const f
no_state_o (RandomO f) = T.RandomO $ const f
no_state_o (SPMaker f) = T.SPMaker $ const f
no_state_o (ReferringSPMaker f) = T.ReferringSPMaker $ const f

no_request :: SPOutputterNS m -> Strict.Maybe LogDOutNS -> NoStateSP m
no_request simulate maybe_log_d = NoStateSP
  { requester = nullReq
  , log_d_req = Strict.Just $ LogDReqNS $ trivial_log_d_req -- Only right for requests it actually made
  , outputter = simulate
  , log_d_out = maybe_log_d
  }

compoundSP :: (Monad m, Fractional num, Real num) => V.Vector DT.Text -> Exp num -> Env -> SP m
compoundSP formals exp env = no_state_sp NoStateSP
  { requester = DeterministicR req
  , log_d_req = Strict.Just $ LogDReqNS trivial_log_d_req
  , outputter = Trivial
  , log_d_out = Strict.Nothing  -- Or Just (0 if it's right, -inf if not?)
  } where
    req args = do
      freshId <- liftM SRId fresh
      let r = SimulationRequest freshId (fmap realToFrac exp) $ Frame (M.fromList $ zip (V.toList formals) args) env
      return [r]

-- It would be nice if these combinators admitted a nice way to pass
-- down the name of the SP they are being used for, without having to
-- repeat it all over its own definition.
on_values :: ([Value num] -> [Value num] -> a) -> ([Node num] -> [Node num] -> a)
on_values f ns1 ns2 = f vs1 vs2 where
    vs1 = map (fromJust' "Argument node had no value" . valueOf) ns1
    vs2 = map (fromJust' "Fulfilment node had no value" . valueOf) ns2

ternary :: (a -> a -> a -> r) -> [a] -> [b] -> r
ternary f [a1,a2,a3] [] = f a1 a2 a3
ternary _ [_,_,_] l = error $ "No requests expected " ++ (show $ length l) ++ " given."
ternary _ l _ = error $ "Three arguments expected " ++ (show $ length l) ++ " given."

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

nary :: (a -> r) -> a -> [b] -> r
nary f x [] = f x
nary _ _ l = error $ "No requests expected " ++ (show $ length l) ++ " given."

-- Is there a better name for these three combinators?
numericala :: (num -> r) -> Value num -> r
numericala f = f' where
    f' (Number v) = f v
    f' _ = error "Incorrect type argument"

numerical2a :: (num -> num -> r) -> Value num -> Value num -> r
numerical2a f = f' where
    f' (Number v) (Number v2) = f v v2
    f' _ _ = error "Incorrect type argument"

numerical3a :: (num -> num -> num -> r) -> Value num -> Value num -> Value num -> r
numerical3a f = f' where
    f' (Number v) (Number v2) (Number v3) = f v v2 v3
    f' _ _ _ = error "Incorrect type argument"

numericalr :: (a -> num) -> a -> Value num
numericalr f = Number . f

-- These Monad contexts are really Functor, but the Applicative Monad
-- Proposal isn't in my version of GHC yet.
numericalrM :: (Monad m) => (a -> m num) -> a -> m (Value num)
numericalrM f x = liftM Number $ f x

numerical2r :: (a -> b -> num) -> a -> b -> Value num
numerical2r f x = Number . f x

numerical2rM :: (Monad m) => (a -> b -> m num) -> a -> b -> m (Value num)
numerical2rM f x y = liftM Number $ f x y

numerical   :: (num -> num) -> Value num -> Value num
numerical   f = numericalr   (numericala  f)

numericalM  :: (Monad m) => (num -> m num) -> Value num -> m (Value num)
numericalM  f = numericalrM  (numericala  f)

numerical2  :: (num -> num -> num) -> Value num -> Value num -> Value num
numerical2  f = numerical2r  (numerical2a f)

numerical2M :: (Monad m) => (num -> num -> m num) -> Value num -> Value num -> m (Value num)
numerical2M f = numerical2rM (numerical2a f)

typed :: (Valuable num a) => (a -> r) -> Value num -> r
typed f = f . (fromJust "Incorrect type argument") . fromValue

typed2 :: (Valuable num1 a, Valuable num2 b) => (a -> b -> r) -> Value num1 -> Value num2 -> r
typed2 = typed . (typed .)

typed3 :: (Valuable num1 a, Valuable num2 b, Valuable num3 c) =>
          (a -> b -> c -> r) -> Value num1 -> Value num2 -> Value num3 -> r
typed3 = typed . (typed2 .)

typedr :: (ValueEncodable num r) => (a -> r) -> a -> Value num
typedr f = toValue . f

typedrM :: (Monad m, ValueEncodable num r) => (a -> m r) -> a -> m (Value num)
typedrM f = liftM toValue . f

typedr2 :: (ValueEncodable num r) => (a -> b -> r) -> a -> b -> Value num
typedr2 f x = toValue . f x

typedr2M :: (Monad m, ValueEncodable num r) => (a -> b -> m r) -> a -> b -> m (Value num)
typedr2M f x y = liftM toValue $ f x y

typedr3 :: (ValueEncodable num r) => (a -> b -> c -> r) -> a -> b -> c -> Value num
typedr3 f x y = toValue . f x y

deterministic :: (forall num. (T.Numerical num) => [Value num] -> [Value num] -> Value num) -> SP m
deterministic f = no_state_sp $ no_request (DeterministicO $ on_values f) Strict.Nothing

bernoulli :: (MonadRandom m) => NoStateSP m
bernoulli = no_request
  (RandomO $ nullary $ liftM Boolean $ getRandomR (False,True))
  (Strict.Just $ LogDOutNS $ nullary $ const (-log 2.0))

weighted :: (MonadRandom m) => NoStateSP m
weighted = no_request
  (RandomO $ on_values $ unary $ numericala $ typedrM weighted_flip)
  (Strict.Just $ LogDOutNS $ on_values $ unary $ numericala $ typed . log_d_weight)

uniform_continuous :: (MonadRandom m) => NoStateSP m
uniform_continuous = no_request
  (RandomO $ on_values $ binary $ numerical2M uniform_c_flip)
  (Strict.Just $ LogDOutNS $ on_values $ binary $ numerical3a log_d_uniform_c)

uniform_discrete :: (MonadRandom m) => NoStateSP m
uniform_discrete = no_request
  (RandomO $ on_values $ binary $ numerical2M uniform_d_flip)
  (Strict.Just $ LogDOutNS $ on_values $ binary $ numerical3a log_d_uniform_d)

normal :: (MonadRandom m) => NoStateSP m
normal = no_request
  (RandomO $ on_values $ binary $ numerical2M normal_flip)
  (Strict.Just $ LogDOutNS $ on_values $ binary $ numerical3a log_d_normal)

xxxFakeGenericity2 :: (Real num, Fractional num) =>
                      (Double -> Double -> Double) -> (num -> num -> num)
xxxFakeGenericity2 f x1 x2 = realToFrac $ f (realToFrac x1) (realToFrac x2)

xxxFakeGenericity3 :: (Real num, Fractional num) =>
                      (Double -> Double -> Double -> Double) -> (num -> num -> Double -> num)
xxxFakeGenericity3 f x1 x2 x3 = realToFrac $ f (realToFrac x1) (realToFrac x2) x3

betaO :: forall m num. (MonadRandom m, Real num, Fractional num) => num -> num -> m (Value num)
betaO alpha beta = do
  -- Adapted from Statistics.Distribution.Beta; not reused because of
  -- funny randomness management convention.
  x <- getRandomR (0.0,1.0)
  return $ Number $ quantile x
    where
      quantile :: Double -> num
      quantile x | x == 0 = 0
                 | x == 1 = 1
                 | 0 < x && x < 1 = xxxFakeGenericity3 invIncompleteBeta alpha beta x
                 | otherwise = error $ "x must be in the range [0,1], got: " ++ show x

log_denisty_beta :: (Floating num, Real num) => num -> num -> num -> num
log_denisty_beta a b x = (a-1)*log x + (b-1)*log (1-x) - xxxFakeGenericity2 logBeta a b

beta :: (MonadRandom m) => NoStateSP m
beta = no_request
  (RandomO $ on_values $ binary $ numerical2a betaO)
  (Strict.Just $ LogDOutNS $ on_values $ binary $ numerical3a log_denisty_beta)

cbeta_bernoulli_flip :: (MonadRandom m, Numerical num) => (Pair num num) -> m Bool
cbeta_bernoulli_flip (ctYes :!: ctNo) = weighted_flip $ ctYes / (ctYes + ctNo)

cbeta_bernoulli_log_d :: (Numerical num1, Numerical num2) => (Pair num1 num1) -> Bool -> num2
cbeta_bernoulli_log_d (ctYes :!: ctNo) = log_d_weight $ realToFrac $ ctYes / (ctYes + ctNo)

cbeta_bernoulli_frob :: (num -> num) -> Bool -> (Pair num num) -> (Pair num num)
cbeta_bernoulli_frob f True  s = s & _1 %~ f
cbeta_bernoulli_frob f False s = s & _2 %~ f

cbeta_bernoulli :: (MonadRandom m, Numerical num) => num -> num -> SP m
cbeta_bernoulli ctYes ctNo = T.SP
  { T.requester = no_state_r nullReq
  , T.log_d_req = Strict.Just $ T.LogDReq $ const trivial_log_d_req -- Only right for requests it actually made
  , T.outputter = T.RandomO $ nullary . (typedrM cbeta_bernoulli_flip)
  , T.log_d_out = Strict.Just $ T.LogDOut $ nullary . typed . cbeta_bernoulli_log_d
  , T.current = (ctYes :!: ctNo)
  , T.incorporate = typed $ cbeta_bernoulli_frob (+1)
  , T.unincorporate = typed $ cbeta_bernoulli_frob (+ (-1))
  , T.incorporateR = const $ const id
  , T.unincorporateR = const $ const id
  }

make_cbeta_bernoulli :: (MonadRandom m) => SP m
make_cbeta_bernoulli = no_state_sp $ no_request
  (SPMaker $ on_values $ binary $ f) -- typed2 cbeta_bernoulli
  (Strict.Nothing)
  where
    f :: (MonadRandom m, T.Numerical num) => Value num -> Value num -> SP m
    f (Number n1) (Number n2) = cbeta_bernoulli n1 n2
    f _ _ = error "Wrong type argument to make_cbeta_bernoulli"

selectO :: [Value num] -> [b] -> Value num
selectO [p,c,a] [] = if fromJust "Predicate was not a boolean" $ fromValue p then c
                     else a
selectO _ _ = error "Wrong number of arguments to SELECT"

-- Here the Ord is because of the Ord constraint on memoized_sp
mem :: (Monad m) => SP m
mem = no_state_sp $ no_request (ReferringSPMaker $ unary $ memoized_sp) Strict.Nothing

-- The memoization cache always stores objects of type Value Double,
-- and converts any other Numerical Value num to them for comparison.
-- This is safe in the use cases I envision, because the keys in the
-- mem cache do not have any interesting derivative information in
-- them anyway.
memoized_sp :: (Monad m) => Address -> SP m
memoized_sp proc = T.SP
  { T.requester = T.ReaderR req
  , T.log_d_req = Strict.Just $ T.LogDReq $ const $ trivial_log_d_req
  , T.outputter = T.Trivial
  , T.log_d_out = Strict.Nothing
  , T.current = (M.empty :: M.Map [Value Double] (Pair SRId Int))
  , T.incorporate = const $ id
  , T.unincorporate = const $ id
  , T.incorporateR = inc
  , T.unincorporateR = dec
  } where
    req cache args = do
      t <- ask
      let ns = map (fromJust "Memoized SP given dangling address" . flip M.lookup (t^.nodes)) args
          vs = map (fromJust' "Memoized SP given valueless argument node" . valueOf) ns
      let cachedSRId = M.lookup (fmap (fmap realToFrac) vs) cache
      case cachedSRId of
        (Just (id :!: _)) -> return [SimulationRequest id (Compose $ Var "unaccessed") Toplevel]
        Nothing -> do
          newId <- liftM SRId fresh
          let names = take (length args) $ map (DT.pack . show) $ ([1..] :: [Int])
              exp = App (Var "memoized-sp") $ V.fromList $ map Var names
              env = Frame (M.fromList $ ("memoized-sp",proc):(zip names args)) Toplevel
          return [SimulationRequest newId (Compose exp) env]
    inc :: (T.Numerical num1, T.Numerical num) => [Value num1] -> [SimulationRequest num1] -> M.Map [Value num] (Pair SRId Int) -> M.Map [Value num] (Pair SRId Int)
    inc vs [req] cache = M.alter incr (fmap (fmap realToFrac) vs) cache where
        incr :: Maybe (Pair SRId Int) -> Maybe (Pair SRId Int)
        incr Nothing = Just (srid req :!: 1)
        incr (Just (srid' :!: k)) | srid' == srid req = Just (srid' :!: k+1)
                               | otherwise = error "Memoized procedure incorporating different requests for the same values"
    inc _ _ _ = error "Memoized procedure expects to incorporate exactly one request"
    dec :: (T.Numerical num1, T.Numerical num) => [Value num1] -> [SimulationRequest num1] -> M.Map [Value num] (Pair SRId Int) -> M.Map [Value num] (Pair SRId Int)
    dec vs [req] cache = M.alter decr (fmap (fmap realToFrac) vs) cache where
        decr :: Maybe (Pair SRId Int) -> Maybe (Pair SRId Int)
        decr Nothing = error "Memoized procedure unincorporating a request it did not make"
        decr (Just (srid' :!: k)) | srid' == srid req = if (k==1) then Nothing
                                                        else Just (srid' :!: k-1)
                                  | otherwise = error "Memoized procedure unincorporating different requests for the same values"
    dec _ _ _ = error "Memoized procedure expects to unincorporate exactly one request"

-- Question for a wizard: is there a way to actually use my stupid
-- "typed" and "typedr" combinators for this?
-- lift :: (forall num a r. (T.Numerical num, Valueable num a, ValueEncodable num r) => a -> r) -> SP m
lift_numerical :: (forall num. T.Numerical num => num -> num) -> SP m
lift_numerical f = deterministic $ unary $ numerical f

lift_numerical2 :: (forall num. T.Numerical num => num -> num -> num) -> SP m
lift_numerical2 f = deterministic $ binary $ numerical2 f

lift_real_real_to_bool :: (forall num. T.Numerical num => num -> num -> Bool) -> SP m
lift_real_real_to_bool f = deterministic $ binary $ typedr2 $ numerical2a f

lift_numerical_variadic_reduction :: (forall num. T.Numerical num => num -> num -> num) -> Double -> SP m
lift_numerical_variadic_reduction f init = deterministic f' where
    f' vals _ = Number $ foldl' f (realToFrac init) $ map fromNumber vals
    fromNumber (Number v) = v
    fromNumber _ = error "Incorrect type argument"

initializeBuiltins :: (MonadState (Trace m1 num) m, MonadRandom m1,
                      Floating num, Enum num, Show num, Real num) => Env -> m Env
initializeBuiltins env = do
  spaddrs <- mapM (state . addFreshSP) sps
  addrs <- mapM (state . addFreshNode . Constant . Procedure) spaddrs
  return $ Frame (M.fromList $ zip names addrs) env
      where namedSps = [ ("bernoulli", no_state_sp bernoulli)
                       , ("uniform_continuous", no_state_sp uniform_continuous)
                       , ("uniform_discrete", no_state_sp uniform_discrete)
                       , ("normal", no_state_sp normal)
                       , ("beta", no_state_sp beta)
                       , ("select", deterministic selectO)
                       , ("list", deterministic $ nary $ List . V.fromList)
                       , ("weighted", no_state_sp weighted)
                       , ("flip", no_state_sp weighted) -- Conventional name.
                       , ("make-cbeta-bernoulli", make_cbeta_bernoulli)
                       , ("mem", mem)
                       , ("sin", lift_numerical sin)
                       , ("sqrt", lift_numerical sqrt)
                       , ("pow", lift_numerical2 (**))
                       , ("+", lift_numerical_variadic_reduction (+) 0)
                       , ("-", lift_numerical2 (-))
                       , ("*", lift_numerical_variadic_reduction (*) 1)
                       , ("=", lift_real_real_to_bool (==))
                       , (">=", lift_real_real_to_bool (>=))
                       -- "Tag" does nothing in HsVenture because
                       -- there are no selectors.
                       , ("tag", deterministic $ ternary $ const $ const id)
                       ]
            names = map fst namedSps
            sps = map snd namedSps
