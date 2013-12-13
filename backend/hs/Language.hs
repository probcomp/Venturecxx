{-# LANGUAGE GeneralizedNewtypeDeriving, MultiParamTypeClasses, FlexibleInstances #-}

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
  deriving (Eq, Ord, Show)

newtype LogDensity = LogDensity Double
    deriving Random

instance Monoid LogDensity where
    mempty = LogDensity 0.0
    (LogDensity x) `mappend` (LogDensity y) = LogDensity $ x + y

log_density_negate :: LogDensity -> LogDensity
log_density_negate (LogDensity x) = LogDensity $ -x

data Exp v = Datum v
           | Var String
           | App (Exp v) [Exp v]
           | Lam [String] (Exp v)
    deriving Show

data Env k v = Toplevel
             | Frame (M.Map k v) (Env k v)
    deriving Show

lookup :: (Ord k) => k -> (Env k v) -> Maybe v
lookup _ Toplevel = Nothing
lookup s (Frame m env') = frob (M.lookup s m) $ lookup s env' where
    frob :: Maybe a -> Maybe a -> Maybe a
    frob (Just x) _ = Just x
    frob Nothing y = y

effectiveEnv :: (Ord k) => Env k v -> M.Map k v
effectiveEnv Toplevel = M.empty
effectiveEnv (Frame m env') = M.union m $ effectiveEnv env'
