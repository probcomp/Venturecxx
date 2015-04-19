{-# LANGUAGE OverloadedStrings #-}

module WireProtocol where

import           Data.Functor.Compose
import qualified Data.ByteString.Lazy         as B
import qualified Data.Map                     as M
import qualified Data.Text                    as T (unpack)

import           Network.Wai
import qualified Network.HTTP.Types           as HTTP
import qualified Network.Wai.Handler.Warp     as Warp (run)
import qualified Data.Aeson                   as Aeson

import qualified Venture                      as V
import qualified VentureGrammar               as G

data Command num = Directive (V.Directive num)
                 | ListDirectives
  deriving Show

run :: (Command Double -> IO B.ByteString) -> IO ()
run act = do
  putStrLn "Venture listening on 3000"
  Warp.run 3000 (application act)

-- The Venture wire protocol is to request a url whose path is the
-- method name and put in the body a list of strings to use for
-- arguments.
off_the_wire :: Request -> IO (Either String (String, [String]))
off_the_wire r = do
  let method = parse_method r
  body <- lazyRequestBody r
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
parse :: String -> [String] -> Either String (Command Double)
parse "assume" [var, expr] = Right $ Directive $ V.Assume var $ Compose $ G.parse expr
parse "assume" args = Left $ "Incorrect number of arguments to assume " ++ show args
parse "list_directives" _ = Right ListDirectives
parse m _ = Left $ "Unknown directive " ++ m

-- This is meant to be interpreted by the client as a VentureException
-- containing the error message.  The parallel code is
-- python/lib/server/utils.py RestServer
error_response :: String -> LoggableResponse
error_response err = LBSResponse HTTP.status500 [("Content-Type", "text/plain")] $ Aeson.encode json where
  json :: M.Map String String
  json = M.fromList [("exception", "fatal"), ("message", err)]

allow_response :: LoggableResponse
allow_response = LBSResponse HTTP.status200 header "" where
    header = [ ("Content-Type", "text/plain")
             , ("Allow", "HEAD, GET, POST, OPTIONS")
             ] ++ boilerplate_headers

application :: ((Command Double) -> IO B.ByteString) -> Request -> (Response -> IO ResponseReceived) -> IO ResponseReceived
application act req k = do
  logRequest req
  if (requestMethod req == "OPTIONS") then
      send $ allow_response
  else do
      strings <- off_the_wire req
      case strings of
        Left err -> send $ error_response err
        Right (method, args) ->
            case parse method args of
              Left err -> send $ error_response err
              Right d -> do body <- act d
                            send $ resp body
  where
    resp body = LBSResponse HTTP.status200 headers body
    headers = [("Content-Type", "application/json")] ++ boilerplate_headers
    send resp = do
      logResponse resp
      k $ prepare resp

---- Logging

logRequest :: Request -> IO ()
logRequest req = do
  putStrLn $ show $ requestMethod req
  putStrLn $ (show $ rawPathInfo req) ++ " " ++ (show $ rawQueryString req)
  body <- lazyRequestBody req
  putStrLn $ show body

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
