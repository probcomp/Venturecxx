{
{-# LANGUAGE OverloadedStrings #-}

module VentureGrammar(parse) where

import qualified Data.Text as DT
import qualified Data.Vector as V

import qualified VentureTokens as T
import Language
import Data.Functor.Compose -- For making Trace expressions
import Trace (if_, let1_, SPAddress)

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
  quo  { T.Symbol "quote" }
  true  { T.Symbol "true" }
  false  { T.Symbol "false" }
  if__  { T.Symbol "if" }
  let1__  { T.Symbol "let" }
  sym  { T.Symbol $$ }

%%

Exp : sym  { Var $ DT.pack $1 }
    | true { Datum $ Boolean True }
    | false { Datum $ Boolean False }
    | int  { Datum $ Number $ fromInteger $1 }
    | flo  { Datum $ Number $1 }
    | '(' quo Exp ')' { Datum $ exp_to_value $3 } -- Or do I want a separate "datum" grammar?
    | '(' Exp Exps ')' { App $2 (V.fromList $ reverse $3) }
    | '(' lam '(' Syms ')' Exp ')' { Lam (V.fromList $ reverse $ map DT.pack $4) $6 }
    | '(' if__ Exp Exp Exp ')' { if' $3 $4 $5 }
    | '(' let1__ '(' '(' sym Exp ')' ')' Exp ')' { let1' (DT.pack $5) $6 $9 }

Exps :  { [] }
     | Exps Exp { $2 : $1 }

Syms : { [] }
     | Syms sym { $2 : $1 }

{

if' p c a = getCompose $ if_ (Compose p) (Compose c) (Compose a)
let1' name val body = getCompose $ let1_ name (Compose val) (Compose body)

-- TODO: Putting sexp-quote into this grammar sucks.  Options:
-- - Add a (quote <exp>) rule whose semantic action downgrades an
--   expression to a value (this is what I did here)
-- - Add a separate segment to the grammar to parse the inside of a quote differently
-- - Eliminate parsing for expressions entirely, and write a converter
--   from list structure that detects keywords.  Taylor recommends this,
--   on the grounds that it simplifies the parser, and decomposes the
--   system into more pieces that are consequently more understandable.
exp_to_value (Datum val) = val
exp_to_value (Var name) = Symbol name
exp_to_value (App op opands) = List $ V.cons (exp_to_value op) $ V.map exp_to_value opands
exp_to_value (Lam formals body) = List $ V.fromList [Symbol "lambda", List (V.map Symbol formals), exp_to_value body]

parseError :: T.Token -> T.Alex a
parseError t = T.Alex (\T.AlexState {T.alex_pos = (T.AlexPn _ line col)} -> Left $ "Parse error at " ++ show line ++ ":" ++ show col ++ " on token " ++ show t)

-- parse :: String -> Exp v -- except v is constrained
-- Fixing the proc type variable to SPAddress is only useful to reuse
-- the definitions of the if_ and let1_ combinators in if' and let1'.
-- Could also have duplicated them, or separated parsing from Trace.Exps entirely.
parse :: (Fractional num) => String -> Exp (Value SPAddress num)
parse s = case T.runAlex s $ parseHelp of
            Left err -> error $ "Error parsing " ++ s ++"\n" ++ err
            Right e -> fmap (fmap realToFrac) e
}
