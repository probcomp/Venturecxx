{-# LANGUAGE NoMonomorphismRestriction #-}
{-# LANGUAGE DeriveFunctor #-}

-- The purpose of this module is to check what GHC's type inference
-- can and can't do with the types that appear in Kmett's ad package.

module GradientTestSmall where

import Numeric.AD.Mode.Reverse (grad)

data Thing num = Thing num
  deriving Functor

fromThing :: Thing num -> num
fromThing (Thing x) = x

myfunc (Thing thing) [x] = x + thing

-- I think the only reason this works is because "thing" ends up typed
-- as (Num a) => Thing a, and computed separately at each call site
-- (with different Num instances).  Turning on the monomorphism
-- restriction breaks this example.
answer :: Num a => [a]
answer = let thing = Thing 0 in
         grad (myfunc $ thing) [fromThing thing]

-- Chaining in a monad prevents the duplicate computation exhibited by
-- answer.  Mapping realToFrac suffices to separate the type demanded
-- by grad from the type available in thing, so this still works.
answer2 = do
  thing <- return $ Thing 0
  return $ grad (myfunc $ realToFrac `fmap` thing) [fromThing thing]

-- For some reason, GHC 7.6.3 completely fails to infer a type for func
-- here, impeding attempts to abstract over calling grad.
frob func = do
  thing <- return $ Thing 0
  return $ grad (func $ realToFrac `fmap` thing) [fromThing thing]

answer3 :: (Monad m, Real a) => m [a]
answer3 = frob myfunc
