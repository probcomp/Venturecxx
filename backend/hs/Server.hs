{-# LANGUAGE OverloadedStrings #-}

-- I want to try to write this with a minimum of new concepts; to wit
-- as a WAI application run by the warp Haskell web server (no web
-- framework: no routing, no sql database)

-- I have found searching for documentation on the actual pieces
-- (rather than the web frameworks themsevles) to be somewhat tedious.
-- References:
-- - Overview http://www.yesodweb.com/book/web-application-interface
-- - Network.Wai package http://hackage.haskell.org/package/wai-2.1.0.1/docs/Network-Wai.html

import           Data.Functor.Compose
import           Control.Concurrent.MVar
import           Control.Monad.State.Lazy
import qualified Data.ByteString.Lazy         as B
import qualified Data.Map                     as M
import qualified Data.Text                    as T (unpack)

import           Network.Wai
import qualified Network.HTTP.Types           as HTTP
import           Network.Wai.Handler.Warp     (run)
import qualified Data.Aeson                   as Aeson

import qualified Utils                        as U
import qualified Language                     as L
import           InferenceInterpreter         hiding (execute)
import qualified Trace                        as T
import qualified Venture                      as V
import qualified VentureGrammar               as G

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

data Command num = Directive (V.Directive num)
                 | ListDirectives
  deriving Show

-- So far, expect the method and arguments to lead to a directive
interpret :: String -> [String] -> Either String (Command Double)
interpret "assume" [var, expr] = Right $ Directive $ V.Assume var $ Compose $ G.parse expr
interpret "assume" args = Left $ "Incorrect number of arguments to assume " ++ show args
interpret "list_directives" _ = Right ListDirectives
interpret m _ = Left $ "Unknown directive " ++ m

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

application :: MVar (V.Model IO Double) -> Request -> (Response -> IO ResponseReceived) -> IO ResponseReceived
application engineMVar req k = do
  logRequest req
  if (requestMethod req == "OPTIONS") then
      send $ allow_response
  else do
      parsed <- off_the_wire req
      case parsed of
        Left err -> send $ error_response err
        Right (method, args) ->
            case interpret method args of
              Left err -> send $ error_response err
              Right d -> do resp <- execute engineMVar d
                            send resp
  where
    send resp = do
      logResponse resp
      k $ prepare resp

execute :: MVar (V.Model IO Double) -> (Command Double) -> IO LoggableResponse
execute engineMVar c = do
  putStrLn $ show c
  case c of
    (Directive d) -> do
      value <- onMVar engineMVar $ runDirective d
      return $ LBSResponse HTTP.status200 [("Content-Type", "text/plain")] $ encodeMaybeValue value
    ListDirectives -> do
      directives <- liftM V._directives $ readMVar engineMVar
      return $ LBSResponse HTTP.status200 [("Content-Type", "text/plain")] $ Aeson.encode $ map (show . U.pp) $ directives

encodeMaybeValue :: Maybe (T.Value Double) -> B.ByteString
encodeMaybeValue Nothing = "null"
encodeMaybeValue (Just v) = encodeValue v

encodeValue :: T.Value Double -> B.ByteString
encodeValue (L.Number x) = Aeson.encode x
encodeValue (L.Symbol s) = Aeson.encode s
encodeValue (L.List vs) = "[" `B.append` (B.intercalate ", " $ map encodeValue vs) `B.append` "]"
encodeValue (L.Procedure _) = "An SP"
encodeValue (L.Boolean True) = "true"
encodeValue (L.Boolean False) = "false"

-- Execute the given state action on the contents of the given MVar,
-- put the answer back, and return the result of the action.
-- The extraction and return are not atomic unless the current thread
-- is the only producer.
onMVar :: MVar a -> (StateT a IO b) -> IO b
onMVar var act = do
  a <- takeMVar var
  (b, a') <- runStateT act a
  putMVar var a'
  return b

main :: IO ()
main = do
  engineMVar <- newMVar V.initial :: IO (MVar (V.Model IO Double))
  putStrLn "Venture listening on 3000"
  run 3000 (application engineMVar)

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
