{-# LANGUAGE DeriveFunctor #-}
{-# LANGUAGE RankNTypes #-}


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
-- One needs either the explicit type signature on thing or turning
-- off the monomorphism restriction.  I think the only reason this
-- works is because "thing", being typed as (Num a) => Thing a, gets
-- computed separately at each call site (with different Num
-- instances).
answer :: Num a => [a]
answer = let thing :: Num x => Thing x
             thing = Thing 0 in
         grad (myfunc $ thing) [fromThing thing]

-- Use pattern 2: Also works.
-- Chaining in a monad prevents the duplicate computation exhibited by
-- answer.  Mapping realToFrac suffices to separate the type demanded
-- by grad from the type available in thing, so this still works.
answer2 :: (Monad m, Fractional a, Real a) => m [a]
answer2 = do
  thing <- return $ Thing 0
  return $ grad (myfunc $ realToFrac `fmap` thing) [fromThing thing]

-- Use pattern 3: Works (after Taylor's help).
-- Without the type signature on frob, GHC 7.6.3 completely fails to
-- infer a type for func here, with a very unhelpful error message.
frob :: (Monad m, Fractional a, Real a) => (forall x. (Num x) => Thing x -> [x] -> x) -> m [a]
frob func = do
  thing <- return $ Thing 0
  return $ grad (func $ realToFrac `fmap` thing) [fromThing thing]

answer3 :: (Monad m, Fractional a, Real a) => m [a]
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
-- This is analogous to answer (also breaks if I remove the type
-- annotation from box and don't turn off the monomorphism
-- restriction).
answer5 :: (Num a) => [a]
answer5 = let box :: (Num a) => Box a
              box = Box inc
          in grad (head . fmap (unBox $ box)) [0]

-- Use pattern 5: ???
-- This situation should be analogous to answer2, but how do I change
-- the Num instance with which the function inside the box is
-- interpreted?
answer6 :: (Monad m, Num a) => m [a]
answer6 = do
  box_3 <- return $ Box inc
  return $ grad (head . fmap (unBox $ xxx box_3)) [0] where
  xxx = id -- ???

-- Ed Kmett suggests making the number type inside the box
-- existential:
data Box2 = Box2 { unBox2 :: forall a. (Num a) => (a -> a) }

-- The analogous thing to answer5 still works.
answer7 :: (Num a) => [a]
answer7 = let box = Box2 inc
          in grad (head . fmap (unBox2 $ box)) [0]

-- The analogous thing to answer6 now works.
answer8 :: (Monad m, Num a) => m [a]
answer8 = do
  box_4 <- return $ Box2 inc
  return $ grad (head . fmap (unBox2 $ box_4)) [0]
