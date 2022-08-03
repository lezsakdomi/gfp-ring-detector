port module Ports exposing (..)

import Json.Decode

port showPrompt : (Maybe String, Maybe String) -> Cmd msg
port promptResponse : (Maybe String -> msg) -> Sub msg
port openWs : String -> Cmd msg
port closeWs : () -> Cmd msg
port messageWs : String -> Cmd msg
port wsMessage : (String -> msg) -> Sub msg
port wsClosed : ((Int, String, Bool) -> msg) -> Sub msg
port initialized : (() -> msg) -> Sub msg
port onmouseup : (Json.Decode.Value -> msg) -> Sub msg
