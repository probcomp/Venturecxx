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

