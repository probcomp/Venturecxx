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

module TestDemo where

import Graphics.Input (Input, input)
import Graphics.Input.Field as Field
import Keyboard

import Demo
import Demo (ripl)


content : Input Field.Content
content = input Field.noContent

enterPressed = countIf id KeyBoard.enter


field : Signal Element
field = Field.field Field.defaultStyle content.handle id "Enter directives here." <~ content.signal

directive : Signal String
directive = (\fieldContent -> fieldContent.string) <~ (sampleOn enterPressed content.signal)

main : Signal Element
main = lift (flow down) <| combine [field, plainText <~ directive]

