{-# LANGUAGE GeneralizedNewtypeDeriving #-}

module Language where

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

data Exp = Exp
data Env = Env
