module Utils (module Utils, module Unique) where

import Data.List (find)
import qualified Data.Map as M
import Control.Lens

import Unique

fromJust :: String -> Maybe a -> a
fromJust _ (Just a) = a
fromJust msg Nothing = error msg

-- A version of the ix lens that errors out if the value is not there
hardix :: (Ord k) => String -> k -> Simple Lens (M.Map k a) a
hardix msg k = lens find replace where
    find = fromJust msg . M.lookup k
    replace m a = case M.lookup k m of
                    (Just _) -> M.insert k a m
                    Nothing -> error msg

-- Suitable for counting with Data.Map.alter
maybeSucc :: Maybe Int -> Maybe Int
maybeSucc Nothing = Just 1
maybeSucc (Just x) = Just $ x+1

embucket :: [(Double,Double)] -> [Double] -> M.Map (Double,Double) Int
embucket buckets values = foldl insert M.empty values where
    insert m v = case find (v `isInside`) buckets of
                   (Just b) -> M.alter maybeSucc b m
                   Nothing -> m
    isInside v (low,high) = low <= v && v < high
