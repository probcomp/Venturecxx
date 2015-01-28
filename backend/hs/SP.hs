{-# LANGUAGE FlexibleContexts #-}
{-# LANGUAGE ScopedTypeVariables #-}

module SP where

import qualified Data.Map as M
import Control.Monad.State.Lazy hiding (state)
import Control.Monad.State.Class
import Control.Monad.Reader
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
-- normal                    a basic continuous stochastic function; absorbing forces log densities
-- select                    one way to do if; forces a brush
-- compoundSP                Venture's lambda; forces ESRs and selective absorbing
-- observe (not an SP)       forces constraints and propagation thereof
-- collapsed beta bernoulli  a higher-order SP, emitting SPs with state
-- mem                       exercises memoization of requests
-- collapsed beta bernoulli  forces AAA under proposing to the hyperparameters
-- make-lazy-hmm             forces latent simulation requests; advanced version forces AEKernels

nullReq :: SPRequesterNS m num
nullReq = DeterministicR $ \_ -> return []

trivial_log_d_req :: (Num num) => a -> b -> num
trivial_log_d_req = const $ const $ 0

data NoStateSP m num = NoStateSP
    { requester :: SPRequesterNS m num
    , log_d_req :: Maybe ([Address] -> [SimulationRequest num] -> num)
    , outputter :: SPOutputterNS m num
    , log_d_out :: Maybe ([Node num] -> [Node num] -> Value num -> num)
    }

data SPRequesterNS m num
    = DeterministicR ([Address] -> UniqueSource [SimulationRequest num])
    | RandomR ([Address] -> UniqueSourceT m [SimulationRequest num])
    | ReaderR ([Address] -> ReaderT (Trace m num) UniqueSource [SimulationRequest num])

data SPOutputterNS m num
    = Trivial
    | DeterministicO ([Node num] -> [Node num] -> Value num)
    | RandomO ([Node num] -> [Node num] -> m (Value num))
    | SPMaker ([Node num] -> [Node num] -> SP m num) -- Are these ever random?
    | ReferringSPMaker ([Address] -> [Address] -> SP m num)

no_state_sp :: NoStateSP m num -> SP m num
no_state_sp NoStateSP { requester = req, log_d_req = ldr, outputter = out, log_d_out = ldo } =
    T.SP { T.requester = no_state_r req
         , T.log_d_req = liftM const ldr
         , T.outputter = no_state_o out
         , T.log_d_out = liftM const ldo
         , T.current = ()
         , T.incorporate = const id
         , T.unincorporate = const id
         , T.incorporateR = const $ const id
         , T.unincorporateR = const $ const id
         }

no_state_r :: SPRequesterNS m num -> T.SPRequester m num a
no_state_r (DeterministicR f) = T.DeterministicR $ const f
no_state_r (RandomR f) = T.RandomR $ const f
no_state_r (ReaderR f) = T.ReaderR $ const f

no_state_o :: SPOutputterNS m num -> T.SPOutputter m num a
no_state_o Trivial = T.Trivial
no_state_o (DeterministicO f) = T.DeterministicO $ const f
no_state_o (RandomO f) = T.RandomO $ const f
no_state_o (SPMaker f) = T.SPMaker $ const f
no_state_o (ReferringSPMaker f) = T.ReferringSPMaker $ const f

compoundSP :: (Monad m, Num num) => [String] -> Exp num -> Env -> SP m num
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

-- It would be nice if these combinators admitted a nice way to pass
-- down the name of the SP they are being used for, without having to
-- repeat it all over its own definition.
on_values :: ([Value num] -> [Value num] -> a) -> ([Node num] -> [Node num] -> a)
on_values f ns1 ns2 = f vs1 vs2 where
    vs1 = map (fromJust "Argument node had no value" . valueOf) ns1
    vs2 = map (fromJust "Fulfilment node had no value" . valueOf) ns2

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
typed :: (Valuable num a) => (a -> r) -> Value num -> r
typed f = f . (fromJust "Incorrect type argument") . fromValue

typed2 :: (Valuable num1 a, Valuable num2 b) => (a -> b -> r) -> Value num1 -> Value num2 -> r
typed2 = typed . (typed .)

typed3 :: (Valuable num1 a, Valuable num2 b, Valuable num3 c) =>
          (a -> b -> c -> r) -> Value num1 -> Value num2 -> Value num3 -> r
typed3 = typed . (typed2 .)

execList :: [Value num] -> [b] -> Value num
execList vs [] = List vs
execList _ _ = error "List SP given fulfilments"

list :: (Monad m, Num num) => SP m num
list = no_state_sp NoStateSP
  { requester = nullReq
  , log_d_req = Just $ trivial_log_d_req -- Only right for requests it actually made
  , outputter = DeterministicO $ on_values execList
  , log_d_out = Nothing
  }

bernoulli_flip :: (MonadRandom m) => m (Value num)
bernoulli_flip = liftM Boolean $ getRandomR (False,True)

bernoulli :: forall m num. (MonadRandom m, Floating num) => SP m num
bernoulli = no_state_sp NoStateSP
  { requester = nullReq
  , log_d_req = Just $ trivial_log_d_req -- Only right for requests it actually made
  , outputter = RandomO $ nullary bernoulli_flip
  , log_d_out = Just $ nullary $ typed (const $ -log 2.0 :: Bool -> num)
  }

weighted_flip :: (MonadRandom m, Fractional num, Ord num) => num -> m (Value num)
weighted_flip weight = do
  (toss :: Double) <- getRandomR (0.0,1.0)
  return $ Boolean $ realToFrac toss < weight

log_d_weight :: (Floating num) => num -> Bool -> num
log_d_weight weight True = log weight
log_d_weight weight False = log (1 - weight)

weighted :: (MonadRandom m, Floating num, Ord num) => SP m num
weighted = no_state_sp NoStateSP
  { requester = nullReq
  , log_d_req = Just $ trivial_log_d_req -- Only right for requests it actually made
  , outputter = RandomO $ on_values $ unary $ typed weighted_flip
  , log_d_out = Just $ on_values $ unary $ typed2 log_d_weight
  }

box_muller_cos :: Double -> Double -> Double
box_muller_cos u1 u2 = r * cos theta where
    r = sqrt (-2 * log u1)
    theta = 2 * pi * u2

normal_flip :: (MonadRandom m, Fractional num) => num -> num -> m (Value num)
normal_flip mu sigma = do
  u1 <- getRandomR (0.0, 1.0)
  u2 <- getRandomR (0.0, 1.0)
  let normal = box_muller_cos u1 u2
  return $ Number $ sigma * realToFrac normal + mu

log_d_normal :: (Floating num) => num -> num -> num -> num
log_d_normal mean sigma x = - (x - mean)^^(2::Int) / (2 * sigma^^(2::Int)) - scale where
    scale = log sigma + (log pi)/2

normal :: (MonadRandom m, Floating num) => SP m num
normal = no_state_sp NoStateSP
  { requester = nullReq
  , log_d_req = Just $ trivial_log_d_req -- Only right for requests it actually made
  , outputter = RandomO $ on_values $ binary $ typed2 normal_flip
  , log_d_out = Just $ on_values $ binary $ typed3 log_d_normal
  }

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

beta :: (MonadRandom m, Floating num, Real num) => SP m num
beta = no_state_sp NoStateSP
  { requester = nullReq
  , log_d_req = Just $ trivial_log_d_req -- Only right for requests it actually made
  , outputter = RandomO $ on_values $ binary $ typed2 betaO
  , log_d_out = Just $ on_values $ binary $ typed3 log_denisty_beta
  }

cbeta_bernoulli_flip :: (MonadRandom m, Fractional num, Ord num) => (num,num) -> m (Value num)
cbeta_bernoulli_flip (ctYes, ctNo) = weighted_flip $ ctYes / (ctYes + ctNo)

cbeta_bernoulli_log_d :: (Floating num) => (num,num) -> Bool -> num
cbeta_bernoulli_log_d (ctYes, ctNo) = log_d_weight $ ctYes / (ctYes + ctNo)

cbeta_bernoulli_frob :: (num -> num) -> Bool -> (num,num) -> (num,num)
cbeta_bernoulli_frob f True  s = s & _1 %~ f
cbeta_bernoulli_frob f False s = s & _2 %~ f

cbeta_bernoulli :: (MonadRandom m, Show num, Floating num, Ord num, Enum num) =>
                   num -> num -> SP m num
cbeta_bernoulli ctYes ctNo = T.SP
  { T.requester = no_state_r nullReq
  , T.log_d_req = Just $ const trivial_log_d_req -- Only right for requests it actually made
  , T.outputter = T.RandomO $ nullary . cbeta_bernoulli_flip
  , T.log_d_out = Just $ nullary . typed . cbeta_bernoulli_log_d
  , T.current = (ctYes, ctNo)
  , T.incorporate = typed $ cbeta_bernoulli_frob succ
  , T.unincorporate = typed $ cbeta_bernoulli_frob pred
  , T.incorporateR = const $ const id
  , T.unincorporateR = const $ const id
  }

make_cbeta_bernoulli :: (MonadRandom m, Show num, Floating num, Ord num, Enum num) => SP m num
make_cbeta_bernoulli = no_state_sp NoStateSP
  { requester = nullReq
  , log_d_req = Just $ trivial_log_d_req -- Only right for requests it actually made
  , outputter = SPMaker $ on_values $ binary $ typed2 cbeta_bernoulli
  , log_d_out = Nothing
  }

selectO :: [Value num] -> [b] -> Value num
selectO [p,c,a] [] = if fromJust "Predicate was not a boolean" $ fromValue p then c
                     else a
selectO _ _ = error "Wrong number of arguments to SELECT"

select :: (Num num) => SP m num
select = no_state_sp NoStateSP
  { requester = nullReq
  , log_d_req = Just $ trivial_log_d_req
  , outputter = DeterministicO $ on_values selectO
  , log_d_out = Nothing -- Or Just (0 if it's right, -inf if not?)
  }

-- Here the Ord is because of the Ord constraint on memoized_sp
mem :: (Monad m, Num num, Show num, Ord num) => SP m num
mem = no_state_sp NoStateSP
  { requester = nullReq
  , log_d_req = Just $ trivial_log_d_req
  , outputter = ReferringSPMaker $ unary $ memoized_sp
  , log_d_out = Nothing
  }

-- The Ord is for using the derived Ord instance for Value, which is
-- needful for using the Values as keys in the memoization cache.
memoized_sp :: (Monad m, Num num, Show num, Ord num) => Address -> SP m num
memoized_sp proc = T.SP
  { T.requester = T.ReaderR req
  , T.log_d_req = Just $ const $ trivial_log_d_req
  , T.outputter = T.Trivial
  , T.log_d_out = Nothing
  , T.current = (M.empty :: M.Map [Value num] (SRId,Int))
  , T.incorporate = const $ id
  , T.unincorporate = const $ id
  , T.incorporateR = inc
  , T.unincorporateR = dec
  } where
    req cache args = do
      t <- ask
      let ns = map (fromJust "Memoized SP given dangling address" . flip M.lookup (t^.nodes)) args
          vs = map (fromJust "Memoized SP given valueless argument node" . valueOf) ns
      let cachedSRId = M.lookup vs cache
      case cachedSRId of
        (Just (id,_)) -> return [SimulationRequest id (Var "unaccessed") Toplevel]
        Nothing -> do
          newId <- liftM SRId fresh
          let names = take (length args) $ map show $ ([1..] :: [Int])
              exp = App (Var "memoized-sp") $ map Var names
              env = Frame (M.fromList $ ("memoized-sp",proc):(zip names args)) Toplevel
          return [SimulationRequest newId exp env]
    inc vs [req] cache = M.alter incr vs cache where
        incr Nothing = Just (srid req, 1)
        incr (Just (srid', k)) | srid' == srid req = Just (srid', k+1)
                               | otherwise = error "Memoized procedure incorporating different requests for the same values"
    inc _ _ _ = error "Memoized procedure expects to incorporate exactly one request"
    dec vs [req] cache = M.alter decr vs cache where
        decr Nothing = error "Memoized procedure unincorporating a request it did not make"
        decr (Just (srid', k)) | srid' == srid req = if (k==1) then Nothing
                                                     else Just (srid', k-1)
                               | otherwise = error "Memoized procedure unincorporating different requests for the same values"
    dec _ _ _ = error "Memoized procedure expects to unincorporate exactly one request"


initializeBuiltins :: (MonadState (Trace m1 num) m, MonadRandom m1,
                      Floating num, Enum num, Show num, Real num) => Env -> m Env
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
                       , ("make-cbeta-bernoulli", make_cbeta_bernoulli)
                       , ("mem", mem)]
            names = map fst namedSps
            sps = map snd namedSps
