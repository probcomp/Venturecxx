-- Copyright (c) 2015 MIT Probabilistic Computing Project.
--
-- This file is part of Venture.
--
-- Venture is free software: you can redistribute it and/or modify
-- it under the terms of the GNU General Public License as published by
-- the Free Software Foundation, either version 3 of the License, or
-- (at your option) any later version.
--
-- Venture is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU General Public License for more details.
--
-- You should have received a copy of the GNU General Public License
-- along with Venture.  If not, see <http://www.gnu.org/licenses/>.

module Utils where

import Json
import Dict
import Either (Either, Left, Right, partition)

just : (a -> b) -> Maybe a -> Maybe b
just f maybeA =
  case maybeA of
    Just a -> Just (f a)
    Nothing -> Nothing

right : (b -> c) -> Either a b -> Either a c
right f eitherAB =
  case eitherAB of
    Left a -> Left a
    Right b -> Right (f b)

-- if Nothing, returns the error message
validateMaybe : a -> Maybe b -> (b -> c) -> Either a c
validateMaybe error maybe f =
  case maybe of
    Nothing -> Left error
    Just b -> Right (f b)

-- if Nothing, returns the error message
validateMaybeChain : a -> Maybe b -> (b -> Either a c) -> Either a c
validateMaybeChain error maybe f =
  case maybe of
    Nothing -> Left error
    Just b -> (f b)

-- carries an error message in the Left
validateEither : Either a b -> (b -> c) -> Either a c
validateEither either f =
  case either of
    Left a -> Left a
    Right b -> Right (f b)

-- carries an error message in the Left
validateEitherChain : Either a b -> (b -> Either a c) -> Either a c
validateEitherChain either f =
  case either of
    Left a -> Left a
    Right b -> (f b)

-- carries the first error message or continues with the whole list
validateList : [Either a b] -> ([b] -> c) -> Either a c
validateList eithers f =
  let (lefts, rights) = partition eithers
  in if isEmpty lefts
    then Right (f rights)
    else Left (head lefts)

getProperty : String -> Dict.Dict String a -> Either String a
getProperty prop dict = validateMaybe ("Key '" ++ prop ++ "' not found in " ++ (show dict)) (Dict.lookup prop dict) id

-- gets a string property of the dict
getPropertyString : String -> Dict.Dict String Json.JsonValue -> Either String String
getPropertyString prop dict =
  validateEitherChain (getProperty prop dict) (\json ->
  case json of
    Json.String str -> Right str
    _ -> Left <| "Property '" ++ prop ++ "' not a string in " ++ (show dict))

