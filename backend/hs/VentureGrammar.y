{
module VentureGrammar(parse) where

import qualified VentureTokens as T
import Language

}

%name parseHelp
%tokentype { T.Token }
%error { parseError }
%monad { T.Alex }
%lexer { T.tokenize } { T.Eof }

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

-- parseError :: [T.Token] -> a
parseError ts = fail $ "Parse error " ++ show ts

-- parse :: String -> Exp v -- except v is constrained
parse s = case T.runAlex s $ parseHelp of
            Left err -> error err
            Right e -> e
}
