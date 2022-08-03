module Page.Analyze.Model.Plane exposing (..)

import Page.Analyze.WsTypes as WsTypes

type alias Plane =
   { name: String
   , data: WsTypes.PlaneData
   }
