{
module VentureTokens (tokenize) where
}

%wrapper "basic"

$digit = [0-9]
$alpha = [a-zA-Z]
$signed = [+-]?$digit

tokens :-

  $white+  ;
  (        { \s -> Open }
  )        { \s -> Close }
