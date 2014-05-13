{
module VentureTokens (tokenize, Token(..)) where
}

%wrapper "basic"

$digit = [0-9]
$alpha = [a-zA-Z]
@signed = [\+\-]? $digit+

tokens :-

  $white+  ;
  \(        { \s -> Open }
  \)        { \s -> Close }

  [\+\-]?$digit*\.$digit+(e@signed)? { \s -> Float $ read s }
  [\+\-]?$digit+\.$digit*(e@signed)? { \s -> Float $ read s }

  @signed  { \s -> Int $ read s }

  $alpha[^ ]* { \s -> Symbol s }

{
data Token
    = Open
    | Close
    | Float Double
    | Int Integer
    | Symbol String

tokenize = alexScanTokens
}
