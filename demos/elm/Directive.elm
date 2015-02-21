module Directive where

import Json
import Dict
import Either (Either, Left, Right)
import Utils (validateEither, validateEitherChain, validateMaybe, validateMaybeChain, validateList, getPropertyString, getProperty)

data Value = Symbol String | Number Float | Boolean Bool | Atom Int | Opaque String Json.JsonValue

validateSymbol json =
  case json of
    Json.String string -> Right <| Symbol string
    _ -> Left <| "Symbol must be string " ++ (show json)

validateNumber json =
  case json of
    Json.Number number -> Right <| Number number
    Json.String string -> validateMaybe "Improperly formatted float." (String.toFloat string) Number
    _ -> Left <| "Number must be a float " ++ (show json)

validateBoolean json =
  case json of
    Json.Boolean bool -> Right <| Boolean bool
    _ -> Left <| "Boolean must be a boolean " ++ (show json)

validateAtom json =
  case json of
    Json.Number float -> Right <| Atom (truncate float)
    Json.String string -> validateMaybe "Improperly formatted integer." (String.toInt string) Atom
    _ -> Left <| "Atom must be an integer: " ++ (show json)

validateOpaque type_ json = Right <| Opaque type_ json

typeToValidator = Dict.fromList
  [("symbol", validateSymbol)
  ,("number", validateNumber)
  ,("bool", validateBoolean)
  ,("atom", validateAtom)
  ]

valueFromDict dict =
  validateEitherChain (getPropertyString "type" dict) (\type_ ->
  let validateValue = Dict.findWithDefault (validateOpaque type_) type_ typeToValidator in
  validateEitherChain (getProperty "value" dict) validateValue)

valueFromJson json = 
  case json of
    Json.String string -> Right <| Symbol string
    --Json.Boolean bool -> Right <| Boolean bool
    --Json.Number number -> Right <| Number number
    Json.Object dict -> valueFromDict dict
    _ -> Left <| "Failed to parse JSON into a Value " ++ (show json)

getPropertyValue : Dict.Dict String Json.JsonValue -> Either String Value
getPropertyValue dict = validateEitherChain (getProperty "value" dict) valueFromJson

valueToString value =
  case value of
    Number number -> show number
    Atom integer -> show integer
    Boolean bool -> String.toLower (show bool)
    Symbol string -> string
    Opaque type_ json -> type_

data Expression = Literal Value | Combination [Expression]

expressionFromJson json =
  case json of
    Json.Array array -> validateList (map expressionFromJson array) Combination
    _ -> validateEither (valueFromJson json) Literal

expressionToString expression =
  case expression of
    Literal value -> valueToString value
    Combination expressions -> "(" ++ join " " (map expressionToString expressions) ++ ")"

type Label = Maybe String
data Directive = Assume String Expression Label | Predict Expression Label | Observe Expression Value Label

getExpression dict = validateEitherChain (getProperty "expression" dict) expressionFromJson

getLabel dict =
  case Dict.lookup "label" dict of
    Nothing -> Right Nothing
    Just json -> case json of
      Json.String label -> Right <| Just label
      _ -> Left <| "Label must be a string, not " ++ (show json)

assumeFromJson : Dict.Dict String Json.JsonValue -> Either String Directive
assumeFromJson dict =
  validateEitherChain (getPropertyString "symbol" dict) (\symbol ->
  validateEitherChain (getExpression dict) (\expression ->
  validateEitherChain (getLabel dict) (\label ->
  Right <| Assume symbol expression label)))

predictFromJson dict =
  validateEitherChain (getExpression dict) (\expression ->
  validateEitherChain (getLabel dict) (\label ->
  Right <| Predict expression label))

observeFromJson dict =
  validateEitherChain (getExpression dict) (\expression ->
  validateEitherChain (getPropertyValue dict) (\value ->
  validateEitherChain (getLabel dict) (\label ->
  Right <| Observe expression value label)))

instructionFromJsonDict : Dict.Dict String (Dict.Dict String Json.JsonValue -> Either String Directive)
instructionFromJsonDict = Dict.fromList
  [("assume", assumeFromJson)
  ,("predict", predictFromJson)
  ,("observe", observeFromJson)
  ]

instructionFromJson instruction dict =
  validateMaybeChain ("Unknown instruction " ++ instruction) (Dict.lookup instruction instructionFromJsonDict) ((|>) dict)

directiveFromJson json =
  case json of
    Json.Object dict ->
      validateEitherChain (getPropertyString "instruction" dict) (\instruction -> 
      validateEitherChain (instructionFromJson instruction dict) (\directive ->
      validateEitherChain (getPropertyValue dict) (\value ->
      Right (directive, value))))
    _ -> Left <| "Failed to parse directive " ++ (Json.toString " " json)

directiveToString directive =
  case directive of
    Assume symbol expression label -> "[assume " ++ symbol ++ " " ++ (expressionToString expression) ++ "]"
    Predict expression label -> "[predict " ++ (expressionToString expression) ++ "]"
    Observe expression value label -> "[observe " ++ (expressionToString expression) ++ " " ++ (valueToString value) ++ "]"

parseDirectives : String -> Either String [(Directive, Value)]
parseDirectives directives =
  validateMaybeChain "list_directives did not return valid json" (Json.fromString directives) (\jsonValue ->
  case jsonValue of
    Json.Array array -> validateList (map directiveFromJson array) id
    _ -> Left "list_directives did not return an array")

