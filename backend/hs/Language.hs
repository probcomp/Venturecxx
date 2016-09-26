{-# LANGUAGE GeneralizedNewtypeDeriving, MultiParamTypeClasses, FlexibleInstances #-}
{-# LANGUAGE DeriveFunctor #-}
{-# LANGUAGE DeriveFoldable #-}
{-# LANGUAGE DeriveTraversable #-}

module Language where

import Prelude hiding (lookup)
import Data.Foldable
import qualified Data.Map.Strict as M
import Data.Monoid
import Data.Traversable
import Data.Text
import qualified Data.Vector as V

-- The "proc" type variable is the type of representations of
-- procedures, which I am allowing to vary because it will be
-- specified in a module that imports this one.
-- The "num" type variable is the type of representations of real
-- numbers, which I am allowing to vary because I want to use AD.
data Value proc real = Number !real
                     | Symbol !Text
                     | List (V.Vector (Value proc real))
                     | Procedure !proc
                     | Boolean !Bool
  deriving (Eq, Ord, Show, Functor, Foldable, Traversable)

instance (Num num) => Num (Value a num) where
    -- Only for fromInteger
    fromInteger = Number . fromInteger

-- The "num" type variable is the type of representations of real
-- numbers, which I am allowing to vary because I want to use AD.
newtype LogDensity num = LogDensity num
    deriving Functor

instance (Num num) => Monoid (LogDensity num) where
    mempty = LogDensity 0
    (LogDensity x) `mappend` (LogDensity y) = LogDensity $ x + y

log_density_negate :: (Num num) => LogDensity num -> LogDensity num
log_density_negate (LogDensity x) = LogDensity $ -x

data Exp v = Datum !v
           | Var !Text
           | App !(Exp v) !(V.Vector (Exp v))
           | Lam !(V.Vector Text) !(Exp v)
    deriving (Show, Functor)

instance (Num a) => Num (Exp a) where
    -- Only for fromInteger
    fromInteger = Datum . fromInteger

data Env k v = Toplevel
             | Frame !(M.Map k v) !(Env k v)
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
