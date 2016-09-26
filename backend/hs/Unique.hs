module Unique (Unique(..), UniqueSeed, UniqueSourceT, UniqueSource
              , runUniqueSourceT, uniqueSeed, fresh, runUniqueSource) where

import Data.Functor.Identity
import Control.Monad.Trans.Class
import Control.Monad.Trans.State.Strict
import Control.Monad.Reader
import Control.Monad.Morph

-- A deterministic source of unique objects that, unlike Data.Unique,
-- does not involve the IO monad.

-- Limitation: streams of uniques that are started from different
-- calls to uniqueSeed will be intercomparable.  Perhaps some branding
-- hack might be used to prevent this.

newtype UniqueSeed = UniqueSeed Integer
  deriving Show

newtype Unique = Unique { asInteger :: Integer }
  deriving (Eq, Ord, Show)

newtype UniqueSourceT m a = UniqueSourceT { unwrap :: (StateT UniqueSeed m a) }

class Monad m => UniqueSourceMonad m where
    fresh :: m Unique

instance MonadTrans UniqueSourceT where
    lift = UniqueSourceT . lift

instance Monad m => Monad (UniqueSourceT m) where
    return = UniqueSourceT . return
    (UniqueSourceT act) >>= f = UniqueSourceT (act >>= (unwrap . f))

instance Monad m => UniqueSourceMonad (UniqueSourceT m) where
    fresh = UniqueSourceT (modify succU >> gets fromSeed)

instance (UniqueSourceMonad m) => UniqueSourceMonad (ReaderT r m) where
    fresh = lift $ fresh

uniqueSeed :: UniqueSeed
uniqueSeed = UniqueSeed 0

fromSeed :: UniqueSeed -> Unique
fromSeed (UniqueSeed i) = Unique i

succU :: UniqueSeed -> UniqueSeed
succU (UniqueSeed s) = UniqueSeed $ succ s

runUniqueSourceT :: UniqueSourceT m a -> UniqueSeed -> m (a, UniqueSeed)
runUniqueSourceT (UniqueSourceT action) = runStateT action

type UniqueSource = UniqueSourceT Identity

runUniqueSource :: UniqueSource a -> UniqueSeed -> (a, UniqueSeed)
runUniqueSource a s = runIdentity $ runUniqueSourceT a s

instance MFunctor UniqueSourceT where
    hoist nat act = UniqueSourceT $ hoist nat (unwrap act)
