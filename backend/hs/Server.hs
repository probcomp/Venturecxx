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

import Data.Aeson

-- The Venture wire protocol is to request a url whose path is the
-- method name and put in the body a list of strings to use for
-- arguments.
off_the_wire :: Request -> IO (Either String (String, [String]))
off_the_wire r = do
  let method = show $ pathInfo r
  body <- lazyRequestBody r
  case eitherDecode body of
    Left err -> return $ Left err
    Right args -> return $ Right (method, args)

-- This is meant to be interpreted by the client as a VentureException
-- containing the error message.  The parallel code is
-- python/lib/server/utils.py RestServer
error_response :: String -> Response
error_response err = responseLBS status500 [("Content-Type", "text/plain")] $ encode json where
  json :: M.Map String String
  json = M.fromList [("exception", "fatal"), ("message", err)]

application :: Request -> IO Response
application r = do
  parsed <- off_the_wire r
  case parsed of
    Left err -> return $ error_response err
    Right (method, args) -> do
                  putStrLn $ method
                  putStrLn $ show $ args
                  return $ responseLBS status200 [("Content-Type", "text/plain")] "Hello World"

main :: IO ()
main = do
  putStrLn "Venture listening on 3000"
  run 3000 application
