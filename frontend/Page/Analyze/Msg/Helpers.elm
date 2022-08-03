module Page.Analyze.Msg.Helpers exposing (..)

import Html
import Html.Events
import Json.Decode exposing (..)

type alias MouseEvent =
   { offsetX: Float
   , offsetY: Float
   }

type alias MouseScrollEvent =
   { offsetX: Float
   , offsetY: Float
   , deltaY: Float
   }

mouseEventDecoder : (MouseEvent -> msg) -> Decoder msg
mouseEventDecoder msg =
    map msg <| map2 MouseEvent
        (field "offsetX" float)
        (field "offsetY" float)

mouseWheelDecoder : (MouseScrollEvent -> msg) -> Decoder msg
mouseWheelDecoder msg =
    map msg <| map3 MouseScrollEvent
        (field "offsetX" float)
        (field "offsetY" float)
        (field "deltaY" float)

pd : String -> (Decoder msg) -> Html.Attribute msg
pd evt msg =
    Html.Events.preventDefaultOn evt <|
        map (\a -> (a, True)) msg
