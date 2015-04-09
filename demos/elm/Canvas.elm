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

module Canvas where

import Color
import Graphics.Collage as gfx

pointColor = Color.red

type Point = { x:Float, y:Float }

pointForm = 
  let inner = gfx.filled pointColor (gfx.circle 2)
      outer = gfx.outlined (gfx.solid pointColor) (gfx.circle 5)
  in
      group [inner, outer]

pointToForm : Point -> gfx.Form
pointToForm point = gfx.move (point.x, point.y) pointForm

canvas width height points = 
