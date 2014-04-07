{-# LANGUAGE OverloadedStrings #-}

-- I want to try to write this with a minimum of new concepts; to wit
-- as a WAI application run by the warp Haskell web server (no web
-- framework: no routing, no sql database)

-- I have found searching for documentation on the actual pieces
-- (rather than the web frameworks themsevles) to be somewhat tedious.
-- References:
-- - Overview http://www.yesodweb.com/book/web-application-interface
-- - Network.Wai package http://hackage.haskell.org/package/wai-2.1.0.1/docs/Network-Wai.html

import Network.Wai
import Network.HTTP.Types (status200)
import Network.Wai.Handler.Warp (run)
import qualified Data.ByteString.Lazy as B

application r = do
  putStrLn $ show $ pathInfo r
  putStrLn $ show $ queryString r
  body <- lazyRequestBody r
  B.putStrLn body
  return $ responseLBS status200 [("Content-Type", "text/plain")] "Hello World"

main = do
  putStrLn "Venture listening on 3000"
  run 3000 application
