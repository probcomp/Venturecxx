module Utils (Unique, UniqueSeed, UniqueSourceT, runUniqueSourceT, uniqueSeed) where

import Control.Monad.Trans.Class
import Control.Monad.Trans.State.Strict

data UniqueSeed = UniqueSeed Integer

data Unique = Unique Integer
  deriving (Eq, Ord)

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

uniqueSeed :: UniqueSeed
uniqueSeed = UniqueSeed 0

fromSeed :: UniqueSeed -> Unique
fromSeed (UniqueSeed i) = Unique i

succU :: UniqueSeed -> UniqueSeed
succU (UniqueSeed s) = UniqueSeed $ succ s

runUniqueSourceT :: UniqueSourceT m a -> UniqueSeed -> m (a, UniqueSeed)
runUniqueSourceT (UniqueSourceT action) = runStateT action
