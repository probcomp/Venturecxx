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
