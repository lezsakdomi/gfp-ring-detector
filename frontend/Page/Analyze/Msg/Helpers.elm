module Page.Analyze.Msg.Helpers exposing (..)

import Html
import Html.Events
import Json.Decode exposing (..)
import Json.Encode

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

touchEventDecoder : (MouseEvent -> msg) -> Decoder msg
touchEventDecoder msg =
    let
        convert touchPosition targetPosition =
            MouseEvent
                (touchPosition.x - targetPosition.x)
                (touchPosition.y - targetPosition.y)
    in
    map msg <| map2 convert
        (field "targetTouches" <| field "0" <| map2 (\x y -> {x = x, y = y})
            (field "clientX" float)
            (field "clientY" float)
        )
        (field "target" <| map2 (\x y -> {x = x, y = y})
            (field "x" float)
            (field "y" float)
            )
        -- todo use offsetTop and offsetLeft, and take offsetParent into account recursively

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
