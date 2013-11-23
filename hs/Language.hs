{-# LANGUAGE GeneralizedNewtypeDeriving #-}

module Language where

import Prelude hiding (lookup)
import qualified Data.Map as M
import Data.Monoid
import Control.Monad.Random -- From cabal install MonadRandom

data Value proc = Number Double
                | Symbol String
                | List [Value proc]
                | Procedure proc
                | Boolean Bool

spValue :: Value proc -> Maybe proc
spValue (Procedure s) = Just s
spValue _ = Nothing

newtype LogDensity = LogDensity Double
    deriving Random

instance Monoid LogDensity where
    mempty = LogDensity 0.0
    (LogDensity x) `mappend` (LogDensity y) = LogDensity $ x + y

log_density_nedate :: LogDensity -> LogDensity
log_density_nedate (LogDensity x) = LogDensity $ -x

data Exp v = Datum v
           | Variable String
           | App (Exp v) [Exp v]
           | Lam [String] (Exp v)

data Env k v = Toplevel
             | Frame (M.Map k v) (Env k v)

lookup :: (Ord k) => k -> (Env k v) -> Maybe v
lookup _ Toplevel = Nothing
lookup s (Frame m env') = frob (M.lookup s m) $ lookup s env' where
    frob :: Maybe a -> Maybe a -> Maybe a
    frob (Just x) _ = Just x
    frob Nothing y = y
