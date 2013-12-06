module Utils (module Utils, module Unique) where

import Data.Map as M
import Control.Lens

import Unique

fromJust :: String -> Maybe a -> a
fromJust _ (Just a) = a
fromJust msg Nothing = error msg

mapFst :: (a -> b) -> (a,c) -> (b,c)
mapFst f (a,c) = (f a, c)

mapSnd :: (a -> b) -> (c,a) -> (c,b)
mapSnd f (c,a) = (c, f a)

-- A version of the ix lens that errors out if the value is not there
hardix :: (Ord k) => String -> k -> Simple Lens (M.Map k a) a
hardix msg k = lens find replace where
    find = fromJust msg . M.lookup k
    replace m a = case M.lookup k m of
                    (Just _) -> M.insert k a m
                    Nothing -> error msg
