{-# LANGUAGE NoMonomorphismRestriction #-}
{-# LANGUAGE DeriveFunctor #-}

-- The purpose of this module is to check what GHC's type inference
-- can and can't do with the types that appear in Kmett's ad package.

module GradientTestSmall where

import Numeric.AD.Mode.Reverse (grad)

-- A data structure holding numbers.
data Thing num = Thing { fromThing :: num }
  deriving Functor

-- A function that, if partially applied, will close over such a data
-- structure.
myfunc :: Num a => Thing a -> [a] -> a
myfunc (Thing thing) [x] = x + thing

-- Use pattern 1: Works.
-- I think the only reason this works is because "thing" ends up typed
-- as (Num a) => Thing a, and computed separately at each call site
-- (with different Num instances).  Turning on the monomorphism
-- restriction breaks this example.
answer :: Num a => [a]
answer = let thing = Thing 0 in
         grad (myfunc $ thing) [fromThing thing]

-- Use pattern 2: Also works.
-- Chaining in a monad prevents the duplicate computation exhibited by
-- answer.  Mapping realToFrac suffices to separate the type demanded
-- by grad from the type available in thing, so this still works.
answer2 :: (Monad m, Fractional a, Real a) => m [a]
answer2 = do
  thing <- return $ Thing 0
  return $ grad (myfunc $ realToFrac `fmap` thing) [fromThing thing]

-- Use pattern 3: Fails mysteriously.
-- For some reason, GHC 7.6.3 completely fails to infer a type for func
-- here, impeding attempts to abstract over calling grad.
frob func = do
  thing <- return $ Thing 0
  return $ grad (func $ realToFrac `fmap` thing) [fromThing thing]

answer3 :: (Monad m, Real a) => m [a]
answer3 = frob myfunc

----------------------------------------------------------------------
-- And now with typeclasses and contravariance                      --
----------------------------------------------------------------------

-- A function depending on Num
inc :: (Num a) => a -> a
inc a = a + 1

-- Taking whose gradient works.
answer4 :: Num a => [a]
answer4 = grad (head . fmap inc) [0]

-- A data structure holding such a function.
data Box a = Box { unBox :: (a -> a) }

-- Use pattern 4: Works.
-- I think this is analogous to answer (also breaks if I remove
-- NoMonomorphismRestriction).
answer5 :: (Num a) => [a]
answer5 = let box = Box inc
          in grad (head . fmap (unBox $ box)) [0]

-- Use pattern 5: ???
-- This situation should be analogous to answer2, but how do I change
-- the Num instance with which the function inside the box is
-- interpreted?
answer6 = do
  box_3 <- return $ Box inc
  return $ grad (head . fmap (unBox $ xxx box_3)) [0] where
  xxx = id -- ???
