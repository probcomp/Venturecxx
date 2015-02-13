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

