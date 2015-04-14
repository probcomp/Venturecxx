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

module Ripl where

import Http
import Either

toUrl host port_ = "http://" ++ host ++ ":" ++ port_ ++ "/"

request url instruction content signal =
  Http.send <|
    lift
      (always <| Http.request "POST" (url ++ instruction) ("[" ++ (join ", " content) ++ "]") [("Content-Type", "application/json")])
      signal

makeRipl host port_ =
  let request_ = request <| toUrl host port_ in
    { execute_instruction instruction = request_ instruction []
    , assume symbol expression = request_ "assume" [symbol, expression]
    , predict expression = request_ "predict" [expression]
    , observe expression value = request_ "observe" [expression, value]
    , forget labelOrId = request_ "forget" [labelOrId]
    , list_directives = request_ "list_directives" ["true"]
    , clear = request_ "clear" []
    }

