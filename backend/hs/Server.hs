{-# LANGUAGE OverloadedStrings #-}

-- I want to try to write this with a minimum of new concepts; to wit
-- as a WAI application run by the warp Haskell web server (no web
-- framework: no routing, no sql database)

-- I have found searching for documentation on the actual pieces
-- (rather than the web frameworks themsevles) to be somewhat tedious.
-- References:
-- - Overview http://www.yesodweb.com/book/web-application-interface
-- - Network.Wai package http://hackage.haskell.org/package/wai-2.1.0.1/docs/Network-Wai.html

import           Control.Concurrent           (forkIO, yield)
import           Control.Concurrent.MVar
import           Control.Lens
import           Control.Monad.State.Strict
import qualified Data.ByteString.Lazy         as B
import           Data.List                    (isPrefixOf)
import qualified Data.Map                     as Map
import qualified Data.Bimap                   as Bimap
import           Data.Bimap                   (Bimap)

import qualified Data.Aeson                   as Aeson

import qualified Language                     as L
import qualified Trace                        as T
import qualified Venture                      as V
import qualified Inference                    as I

import           WireProtocol                 (Command(..), run, as_stack_dict, symbol)
import qualified WireProtocol                 as W

type Engine = ((V.Model IO Double), Bimap T.Address String)

execute :: MVar Engine  -> (Command Double) -> IO B.ByteString
execute engineMVar c = do
  putStrLn $ show c
  case c of
    (Directive d label) -> do
      value <- onMVar engineMVar act
      return $ encodeValue value
      where act = do
              addr <- _1 `zoom` V.runDirective' d
              case label of
                Nothing -> return ()
                (Just l) -> _2 %= Bimap.insert addr l
              _1 `uses` (V.lookupValue addr)
    ListDirectives -> liftM directive_report $ readMVar engineMVar
    StopCI -> return "" -- No continuous inference to stop yet
    Clear -> do
      onMVar engineMVar $ put (V.initial, Bimap.empty)
      return ""
    SetMode _ -> return "" -- Only one surface syntax is supported!
    Infer prog -> interpret_inference engineMVar prog

interpret_inference :: MVar Engine -> String -> IO B.ByteString
interpret_inference engineMVar prog =
    if "(loop " `isPrefixOf` prog then do
      _ <- forkIO loop
      return ""
    else do
      onMVar engineMVar $ _1 `zoom` V.resimulation_mh I.default_one -- Only MH supported
      return ""
    where loop = do _ <- interpret_inference engineMVar $ drop 6 prog -- TODO parse it for real
                    yield
                    loop

directive_report :: (Show num, Real num) => (V.Model m num, Bimap T.Address String) -> B.ByteString
directive_report (model, labels) = Aeson.encode $ map to_stack_dict $ directives where
    directives = Map.toList $ V._directives model
    to_stack_dict (addr, directive) = result
        where value = W.get_field (as_stack_dict $ V.lookupValue addr model) "value"
              unlabeled = as_stack_dict directive `W.add_field` ("value", value)
              result = maybe unlabeled (\l -> unlabeled `W.add_field` ("label", symbol l))
                       $ Bimap.lookup addr labels

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
  engineMVar <- newMVar (V.initial :: (V.Model IO Double), Bimap.empty)
  run (liftM Right . (execute engineMVar))

