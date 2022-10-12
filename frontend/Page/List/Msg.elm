module Page.List.Msg exposing (..)

import Json.Decode
import Page.List.WsTypes exposing (WsMessage)

type Msg
    = WsMessage (Result Json.Decode.Error WsMessage)
    | WsClosed
    | ClientMsg ClientMsg

type ClientMsg
    = FilterChanged String
    | StartAnalysis
