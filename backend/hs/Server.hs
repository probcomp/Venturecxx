{-# LANGUAGE OverloadedStrings #-}

-- I want to try to write this with a minimum of new concepts; to wit
-- as a WAI application run by the warp Haskell web server (no web
-- framework: no routing, no sql database)

-- I have found searching for documentation on the actual pieces
-- (rather than the web frameworks themsevles) to be somewhat tedious.
-- References:
-- - Overview http://www.yesodweb.com/book/web-application-interface
-- - Network.Wai package http://hackage.haskell.org/package/wai-2.1.0.1/docs/Network-Wai.html

import           Control.Concurrent.MVar
import           Control.Monad.State.Lazy
import qualified Data.ByteString.Lazy         as B
import qualified Data.Map                     as Map

import           Data.Aeson                   ((.=))
import qualified Data.Aeson                   as Aeson

import qualified Language                     as L
import           InferenceInterpreter         hiding (execute)
import qualified Trace                        as T
import qualified Venture                      as V
import qualified Inference                    as I

import           WireProtocol                 (Command(..), run, as_stack_dict)
import qualified WireProtocol                 as W

execute :: MVar (V.Model IO Double) -> (Command Double) -> IO B.ByteString
execute engineMVar c = do
  putStrLn $ show c
  case c of
    (Directive d) -> do
      value <- onMVar engineMVar $ runDirective d
      return $ encodeMaybeValue value
    ListDirectives -> liftM directive_report $ readMVar engineMVar
    StopCI -> return "" -- No continuous inference to stop yet
    Clear -> do
      onMVar engineMVar (put V.initial)
      return ""
    SetMode _ -> return "" -- Only one surface syntax is supported!
    Infer _ -> do
      onMVar engineMVar $ V.resimulation_mh I.default_one -- Only MH supported
      return ""

directive_report :: (Show num, Real num) => V.Model m num -> B.ByteString
directive_report model = Aeson.encode $ map to_stack_dict $ directives where
    directives = Map.toList $ V._directives model
    to_stack_dict (addr, directive) = as_stack_dict directive `W.add_field` ("value" .= value)
        where value = W.get_field (as_stack_dict $ V.lookupValue addr model) "value"

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
  run (liftM Right . (execute engineMVar))

