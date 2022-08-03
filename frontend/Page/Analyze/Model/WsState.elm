module Page.Analyze.Model.WsState exposing (..)

import Page.Analyze.WsTypes as WsTypes

type WsState
    = Open
    | Closed WsTypes.WsCloseReason
