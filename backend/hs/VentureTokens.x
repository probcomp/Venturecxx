{
module VentureTokens where
}

%wrapper "monad"

$digit = [0-9]
$alpha = [a-zA-Z]
@signed = [\+\-]? $digit+

tokens :-

  $white+  ;
  \(        { axch_token (\s -> Open) }
  \)        { axch_token (\s -> Close) }

  [\+\-]?$digit*\.$digit+(e@signed)? { axch_token (\s -> Float $ read s) }
  [\+\-]?$digit+\.$digit*(e@signed)? { axch_token (\s -> Float $ read s) }

  @signed  { axch_token (\s -> Int $ read s) }

  $alpha[^ ]* { axch_token (\s -> Symbol s) }

{
data Token
    = Open
    | Close
    | Float Double
    | Int Integer
    | Symbol String
    | Eof
  deriving Show

axch_token :: (String -> Token) -> AlexInput -> Int -> Alex Token
axch_token f (_, _, _, s) len = return $ f s

alexEOF :: Alex Token
alexEOF = return Eof

tokenize :: (Token -> Alex a) -> Alex a
tokenize cont = do
    token <- alexMonadScan
    cont token
}
