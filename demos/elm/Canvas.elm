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
