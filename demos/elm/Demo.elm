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

module Demo where

import Ripl (makeRipl)
import Directive (Directive, parseDirectives, directiveToString, valueToString)

import Http
import Either (Left, Right)

data VentureType = Real | Bool | Atom | Opaque

type Model = {directives:[Directive]}

ripl = makeRipl "localhost" "8082"

directiveSignal = ripl.list_directives (every second)

formatText = leftAligned . monospace . toText

displayDirectives directives =
  case parseDirectives directives of
    Left error -> formatText error
    Right dirsAndValues -> flow right <|
      let (dirs, vals) = unzip dirsAndValues in
        [flow down <| map (formatText . directiveToString) dirs
        ,flow down <| map (formatText . valueToString) vals
        ]

-- Display a response.
display response = 
  case response of
    Http.Success directives -> displayDirectives directives
    Http.Waiting -> asText "Waiting for Http response."
    Http.Failure _ _ -> asText response

main = lift display directiveSignal
