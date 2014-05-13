{-# LANGUAGE OverloadedStrings #-}

-- I want to try to write this with a minimum of new concepts; to wit
-- as a WAI application run by the warp Haskell web server (no web
-- framework: no routing, no sql database)

-- I have found searching for documentation on the actual pieces
-- (rather than the web frameworks themsevles) to be somewhat tedious.
-- References:
-- - Overview http://www.yesodweb.com/book/web-application-interface
-- - Network.Wai package http://hackage.haskell.org/package/wai-2.1.0.1/docs/Network-Wai.html

import qualified Data.Map as M
import Network.Wai
import Network.HTTP.Types (status200, status500)
import Network.Wai.Handler.Warp (run)
import Data.Text (unpack)
import Data.Aeson hiding (Value, Number)
import Control.Concurrent.MVar
import Control.Monad.State.Lazy
import qualified Data.ByteString.Lazy as B

import Language hiding (Value)
import Trace
import Engine hiding (execute)
import qualified VentureGrammar as G
import qualified VentureTokens as T

-- The Venture wire protocol is to request a url whose path is the
-- method name and put in the body a list of strings to use for
-- arguments.
off_the_wire :: Request -> IO (Either String (String, [String]))
off_the_wire r = do
  let method = parse_method r
  body <- lazyRequestBody r
  case eitherDecode body of
    Left err -> return $ Left err
    Right args -> case method of
                    Nothing -> return $ Left $ "Cannot parse method from path " ++ (show $ pathInfo r)
                    (Just m) -> return $ Right (m, args)

parse_method :: Request -> Maybe String
parse_method r = parse $ pathInfo r where
  parse [method] = Just $ unpack method
  parse _ = Nothing

-- This is meant to be interpreted by the client as a VentureException
-- containing the error message.  The parallel code is
-- python/lib/server/utils.py RestServer
error_response :: String -> Response
error_response err = responseLBS status500 [("Content-Type", "text/plain")] $ encode json where
  json :: M.Map String String
  json = M.fromList [("exception", "fatal"), ("message", err)]

application :: MVar (Engine IO) -> Request -> IO Response
application engineMVar r = do
  parsed <- off_the_wire r
  case parsed of
    Left err -> return $ error_response err
    Right (method, args) -> execute engineMVar method args

interpret :: String -> [String] -> Either String Directive
interpret "assume" [var, expr] = Right $ Assume var $ G.parse $ T.tokenize expr
interpret "assume" args = Left $ "Incorrect number of arguments to assume " ++ show args
interpret m _ = Left $ "Unknown directive " ++ m

execute :: MVar (Engine IO) -> String -> [String] -> IO Response
execute engineMVar method args =
  case interpret method args of
    Left err -> return $ error_response err
    Right d -> do
      putStrLn $ show d
      value <- onMVar engineMVar $ runDirective d
      return $ responseLBS status200 [("Content-Type", "text/plain")] $ encodeMaybeValue value

encodeMaybeValue :: Maybe Value -> B.ByteString
encodeMaybeValue Nothing = "null"
encodeMaybeValue (Just v) = encodeValue v

encodeValue :: Value -> B.ByteString
encodeValue (Number x) = encode x
encodeValue (Symbol s) = encode s
encodeValue (List vs) = "[" `B.append` (B.intercalate ", " $ map encodeValue vs) `B.append` "]"
encodeValue (Procedure p) = "An SP"
encodeValue (Boolean True) = "true"
encodeValue (Boolean False) = "false"

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
  engineMVar <- newMVar initial
  putStrLn "Venture listening on 3000"
  run 3000 (application engineMVar)
