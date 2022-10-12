module Page.ListAnalyze.Msg exposing (..)

import Json.Decode as Decode
import Page.Analyze.WsTypes exposing (WsCloseReason, WsMessage)
import Page.List.Msg exposing (ClientMsg)
import Time

type Msg
    = ClientMsg ClientMsg
   | WsMessage (Result Decode.Error WsMessage)
   | WsClosed WsCloseReason
