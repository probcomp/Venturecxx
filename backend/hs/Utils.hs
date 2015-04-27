{-# LANGUAGE RankNTypes #-}
{-# LANGUAGE ScopedTypeVariables #-}
{-# LANGUAGE FlexibleInstances #-}
{-# LANGUAGE MultiParamTypeClasses #-}
{-# LANGUAGE UndecidableInstances #-} -- Like in the mtl

module Utils (module Utils, module Unique) where

import Debug.Trace
import Data.List (find)
import Data.Monoid
import qualified Data.Map as M
import qualified Data.Maybe.Strict as Strict
import qualified Data.Set as S
import qualified Data.Vector as V
import Control.Lens
import Control.Monad.Coroutine -- from cabal install monad-coroutine
import Control.Monad.Morph
import qualified Control.Monad.State.Class as Cl
import Control.Monad.Trans.State.Strict
import Control.Monad.Trans.Writer.Strict
import Text.PrettyPrint -- presumably from cabal install pretty

import Unique
import qualified InsertionOrderedSet as O

fromJust :: String -> Maybe a -> a
fromJust _ (Just a) = a
fromJust msg Nothing = error msg

fromJust' :: String -> Strict.Maybe a -> a
fromJust' _ (Strict.Just a) = a
fromJust' msg Strict.Nothing = error msg

-- A version of the ix lens that errors out if the value is not there
hardix :: (Ord k) => String -> k -> Simple Lens (M.Map k a) a
hardix msg k = lens find replace where
    find = fromJust msg . M.lookup k
    replace m a = case M.lookup k m of
                    (Just _) -> M.insert k a m
                    Nothing -> error msg

-- Suitable for counting with Data.Map.alter
maybeSucc :: Num a => Maybe a -> Maybe a
maybeSucc Nothing = Just 1
maybeSucc (Just x) = Just $ x+1

returnT :: (Monad n0, MFunctor t0) => t0 Identity b -> t0 n0 b
returnT = hoist (return . runIdentity)

modifyM :: Monad m => (s -> m s) -> StateT s m ()
modifyM act = get >>= (lift . act) >>= put

embucket :: (Num a, Ord b) => [(b, b)] -> [b] -> M.Map (b, b) a
embucket buckets values = foldl insert M.empty values where
    insert m v = case find (v `isInside`) buckets of
                   (Just b) -> M.alter maybeSucc b m
                   Nothing -> m
    isInside v (low,high) = low <= v && v <= high

buckets :: Int -> [Double] -> [(Double,Double)]
buckets ct values = zip lows (tail lows ++ [high]) where
    low = minimum values
    high = maximum values
    step = (high - low) / fromIntegral ct
    lows = [low,low+step..high]

histogram :: Int -> [Double] -> M.Map (Double,Double) Int
histogram ct values = embucket (buckets ct values) values where

discreteHistogram :: (Eq k, Ord k) => [k] -> M.Map k Int
discreteHistogram ks = foldl insert M.empty ks where
    insert m k = M.alter maybeSucc k m

printHistogram :: (Show k, Show a) => M.Map k a -> IO ()
printHistogram = mapM_ (putStrLn . show) . M.toList

-- TODO Check this with quickcheck (constraining ct to be positive)
-- See, e.g. http://stackoverflow.com/questions/3120796/haskell-testing-workflow
property_histogram_conserves_data :: Int -> [Double] -> Bool
property_histogram_conserves_data ct values = length values == (sum $ M.elems $ histogram ct values)

traceShowIt :: (Show a) => a -> a
traceShowIt it = traceShow it it

tracePrettyIt :: (Pretty a) => a -> a
tracePrettyIt it = traceShow (pp it) it

class Pretty a where
    pp :: a -> Doc

instance (Pretty a) => Pretty [a] where
    pp as = brackets $ sep $ map pp as

instance (Pretty a) => Pretty (V.Vector a) where
    pp as = brackets $ sep $ V.toList $ fmap pp as

instance Pretty Doc where
    pp = id

instance (Pretty a) => Pretty (O.Set a) where
    pp as = brackets $ sep $ map pp $ O.toList as

instance (Pretty a) => Pretty (S.Set a) where
    pp as = brackets $ sep $ map pp $ S.toList as

runWS :: WriterT w (StateT s m) a -> s -> m ((a, w), s)
runWS act state = runStateT (runWriterT act) state

-- Generalize foldRun to the case where the step function is itself a
-- coroutine, over the same underlying monad.
foldRunMC ::  forall s s2 m a x. (Monad m, Functor s2) =>
            (a -> s (Coroutine s m x) -> (Coroutine s2 m) ((Coroutine s m x), a)) ->
            a ->
            Coroutine s m x ->
            Coroutine s2 m (x, a)
foldRunMC spring start c = do
  step <- lift $ resume c
  case step of
    Right result -> return (result, start)
    Left susp -> do
      (c', start') <- spring start susp
      foldRunMC spring start' c'

coroutineRunWS
  :: (Monad m, Functor s, Monoid w) =>
     Coroutine s (WriterT w (StateT state m)) a
     -> w -> state -> Coroutine s m ((a, w), state)
coroutineRunWS c log state = Coroutine act where
    act = do
      ((res, log'), state') <- runWS (resume c) state
      case res of
        Right result -> return $ Right ((result, log `mappend` log'), state')
        Left susp -> return $ Left $ fmap (\c' -> coroutineRunWS c' (log `mappend` log') state') susp

instance (Functor s, Cl.MonadState state m) => Cl.MonadState state (Coroutine s m) where
    get = lift Cl.get
    put = lift . Cl.put
