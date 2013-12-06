module Utils (module Utils, module Unique) where

import Unique

fromJust :: String -> Maybe a -> a
fromJust _ (Just a) = a
fromJust msg Nothing = error msg

mapFst :: (a -> b) -> (a,c) -> (b,c)
mapFst f (a,c) = (f a, c)

mapSnd :: (a -> b) -> (c,a) -> (c,b)
mapSnd f (c,a) = (c, f a)
