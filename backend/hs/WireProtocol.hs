{-# LANGUAGE OverloadedStrings #-}
{-# LANGUAGE TypeSynonymInstances #-}
{-# LANGUAGE FlexibleInstances #-}

module WireProtocol where

import           Control.Monad.Trans.Either   -- from the 'either' package
import           Data.Functor.Compose
import qualified Data.ByteString.Lazy         as B
import qualified Data.HashMap.Strict          as HashMap -- For the add_field and get_field combinators
import qualified Data.Map.Strict              as M
import           Data.Maybe                   (fromJust)
import qualified Data.Text                    as T (Text, pack, unpack)
import qualified Data.Vector                  as Vec

import           Network.Wai
import qualified Network.HTTP.Types           as HTTP
import qualified Network.Wai.Handler.Warp     as Warp (run)
import qualified Data.Aeson                   as Aeson
import qualified Data.Aeson.Types             as J

import           Utils                        (Unique(..))
import qualified Venture                      as V
import qualified VentureGrammar               as G
import qualified Trace                        as Tr -- For the stack dict class
import qualified Language                     as L  -- For the stack dict class

---- Public interface

type Label = T.Text
data Command num = Directive (V.Directive num) (Maybe Label)
                 | Forget Tr.Address
                 | ListDirectives
                 | StopCI
                 | Clear
                 | SetMode T.Text
                 | Infer T.Text
  deriving Show

run :: (Fractional num) => (Command num -> IO (Either String B.ByteString)) -> IO ()
run act = do
  putStrLn "Venture listening on 3000"
  Warp.run 3000 (application act)

---- Parsing

-- The Venture wire protocol is to request a url whose path is the
-- method name and put in the body a list of json objects to use for
-- arguments.
off_the_wire :: Aeson.FromJSON a => Request -> IO (Either String (String, [a]))
off_the_wire r = do
  let method = parse_method r
  body <- lazyRequestBody r
  B.putStrLn body
  case decode_body body of
    Left err -> return $ Left err
    Right args -> case method of
                    Nothing -> return $ Left $ "Cannot parse method from path " ++ (show $ pathInfo r)
                    (Just m) -> return $ Right (m, args)

parse_method :: Request -> Maybe String
parse_method r = parse $ pathInfo r where
  parse [method] = Just $ T.unpack method
  parse _ = Nothing

-- Allow empty request body, meaning the same as no arguments
decode_body :: Aeson.FromJSON a => B.ByteString -> Either String [a]
decode_body "" = Right []
decode_body str = Aeson.eitherDecode str

-- So far, expect the method and arguments to lead to a directive
parse :: (Fractional num) => String -> [J.Value] -> Either String (Command num)
parse "assume" [J.String var, J.String expr] =
    Right $ Directive (V.Assume var $ Compose $ G.parse $ T.unpack expr) Nothing
parse "assume" [J.String var, J.String expr, J.String label] =
    Right $ Directive (V.Assume var $ Compose $ G.parse $ T.unpack expr) $ Just label
parse "assume" args =
    Left $ "Incorrect number of arguments to assume " ++ show args
parse "observe" [J.String expr, J.String val] =
    Right $ Directive (V.Observe expr' val') Nothing where
        expr' = Compose $ G.parse $ T.unpack expr
        val' = fromDatum $ G.parse $ T.unpack val
        fromDatum (L.Datum v) = v
parse "observe" [J.String expr, J.String val, J.String label] =
    Right $ Directive (V.Observe expr' val') $ Just label where
        expr' = Compose $ G.parse $ T.unpack expr
        val' = fromDatum $ G.parse $ T.unpack val
        fromDatum (L.Datum v) = v
parse "observe" args =
    Left $ "Incorrect number of arguments to observe " ++ show args
parse "predict" [J.String expr] =
    Right $ Directive (V.Predict $ Compose $ G.parse $ T.unpack expr) Nothing
parse "predict" [J.String expr, J.String label] =
    Right $ Directive (V.Predict $ Compose $ G.parse $ T.unpack expr) $ Just label
parse "predict" args =
    Left $ "Incorrect number of arguments to predict " ++ show args
parse "list_directives" _ = Right ListDirectives
parse "stop_continuous_inference" _ = Right StopCI
parse "clear" _ = Right Clear
parse "set_mode" [J.String mode] = Right $ SetMode mode
parse "set_mode" args = Left $ "Incorrect number of arguments to set_mode " ++ show args
parse "infer" [J.String prog] = Right $ Infer prog
parse "infer" args = Left $ "Incorrect number of arguments to infer " ++ show args
parse "forget" [J.String did] = Right $ Forget $ Tr.Address $ Unique $ read $ T.unpack did
parse "forget" [J.Number did] = Right $ Forget $ Tr.Address $ Unique $ floor did
parse "forget" args = Left $ "Incorrect number of arguments to forget " ++ show args
parse m _ = Left $ "Unknown directive " ++ m

---- Response helpers

allow_response :: LoggableResponse
allow_response = LBSResponse HTTP.status200 header "" where
    header = [ ("Content-Type", "text/plain")
             , ("Allow", "HEAD, GET, POST, OPTIONS")
             ] ++ boilerplate_headers

-- This is meant to be interpreted by the client as a VentureException
-- containing the error message.  The parallel code is
-- python/lib/server/utils.py RestServer
error_response :: String -> LoggableResponse
error_response err = LBSResponse HTTP.status500 [("Content-Type", "application/json")] $ Aeson.encode json where
  json :: M.Map String String
  json = M.fromList [("exception", "fatal"), ("message", err)]

success_response :: B.ByteString -> LoggableResponse
success_response body = LBSResponse HTTP.status200 headers body where
    headers = [("Content-Type", "application/json")] ++ boilerplate_headers

---- Main action

application :: (Fractional num) => ((Command num) -> IO (Either String B.ByteString))
            -> Request -> (Response -> IO ResponseReceived) -> IO ResponseReceived
application act req k = do
  logRequest req
  if (requestMethod req == "OPTIONS") then
      send allow_response
  else eitherT (send . error_response) (send . success_response) (do
      (method, args) <- EitherT $ off_the_wire req
      d <- hoistEither $ parse method args
      EitherT $ act d)
  where
    send resp = do
      -- logResponse resp
      k $ prepare resp

---- Venture dict representation

class StackDict a where
  as_stack_dict :: a -> J.Value

symbol :: T.Text -> J.Value
symbol str = J.object [ ("type", J.String "symbol")
                      , ("value", J.String str)
                      ]

instance (Show num, Real num) => StackDict (V.Directive num) where
    as_stack_dict (V.Assume var exp) =
        J.object [ ("instruction", J.String "assume")
                 , ("expression", as_stack_dict exp)
                 , ("symbol", symbol $ var)
                 ]
    as_stack_dict (V.Observe exp val) =
        J.object [ ("instruction", J.String "observe")
                 , ("expression", as_stack_dict exp)
                 , ("value", as_stack_dict val)
                 ]
    as_stack_dict (V.Predict exp) =
        J.object [ ("instruction", J.String "predict")
                 , ("expression", as_stack_dict exp)
                 ]

instance (Show num, Real num) => StackDict (Tr.Exp num) where
    as_stack_dict (Compose (L.Datum val)) = as_stack_dict val -- TODO Quote?
    as_stack_dict (Compose (L.Var var)) = symbol var
    as_stack_dict (Compose (L.App op opands)) =
        Aeson.toJSON $ map (as_stack_dict . Compose) (op:Vec.toList opands)
    as_stack_dict (Compose (L.Lam formals body)) =
        Aeson.toJSON $ ([symbol "lambda", st_formals, as_stack_dict (Compose body)])
        where st_formals = Aeson.toJSON $ map symbol $ Vec.toList formals

instance (Show num, Real num) => StackDict (L.Value proc num) where
    as_stack_dict (L.Number n) =
        J.object [ ("type", J.String "number")
                 , ("value", J.Number $ realToFrac n)
                 ]
    as_stack_dict (L.Symbol str) = symbol str
    as_stack_dict (L.List vals) = Aeson.toJSON $ Vec.toList $ fmap as_stack_dict vals
    as_stack_dict (L.Procedure _) =
        J.object [ ("type", J.String "sp")
                 , ("value", J.String "unknown")
                 ]
    as_stack_dict (L.Boolean b) =
        J.object [ ("type", J.String "boolean")
                 , ("value", J.Bool b)
                 ]

add_field :: J.Value -> J.Pair -> J.Value
add_field (J.Object m) (k, v) = J.Object $ HashMap.insert k v m

get_field :: J.Value -> T.Text -> J.Value
get_field (J.Object m) k = fromJust $ HashMap.lookup k m

---- Logging

logRequest :: Request -> IO ()
logRequest req = do
  putStrLn $ show $ requestMethod req
  putStrLn $ (show $ rawPathInfo req) ++ " " ++ (show $ rawQueryString req)

-- I couldn't figure out how to log responses generically, so
-- intercept.
data LoggableResponse = LBSResponse HTTP.Status HTTP.ResponseHeaders B.ByteString
  -- Only one constructor because I only use LBS responses now

prepare :: LoggableResponse -> Response
prepare (LBSResponse s r b) = responseLBS s r b

logResponse :: LoggableResponse -> IO ()
logResponse (LBSResponse s r b) = do
  putStrLn $ show $ s
  putStrLn $ show $ r
  B.putStrLn b

boilerplate_headers =
    [ ("access-control-max-age", "21600")
    , ("access-control-allow-origin", "*")
    , ("access-control-allow-methods", "HEAD, GET, POST, OPTIONS")
    , ("access-control-allow-headers", "CONTENT-TYPE")
    ]
