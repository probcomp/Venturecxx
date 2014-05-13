{
module VentureGrammar(parse) where

import qualified VentureTokens as T
import Language
}

%name parse
%tokentype { T.Token }
%error { parseError }

%token
  '('  { T.Open }
  ')'  { T.Close }
  int  { T.Int $$ }
  flo  { T.Float $$ }
  lam  { T.Symbol "lambda" }
  sym  { T.Symbol $$ }

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
parseError :: [T.Token] -> a
parseError _ = error "Parse error"
}
