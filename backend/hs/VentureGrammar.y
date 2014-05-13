{
module VentureGrammar(parse) where

import VentureTokens
}

%name parse
%tokentype { Token }
%error { parseError }

%token
  '('  { Open }
  ')'  { Close }
  int  { Int $$ }
  flo  { Float $$ }
  lam  { Symbol "lambda" }
  sym  { Symbol $$ }

%%

Exp : sym  { Var $1 }
    | int  { Datum $ Number $ fromInteger $1 }
    | flo  { Datum $ Number $1 }
    | '(' Exp Exps ')' { App $2 (reverse $3) }
    | '(' lam '(' Syms ')' Exp ')' { Lam (reverse $4) $6 }

Exps :  { [] }
     | Exps Exp { $2 : $1 }

Syms : { [] }
     | Syms sym { $2 : $1 }

{
parseError :: [Token] -> a
parseError _ = error "Parse error"
}
