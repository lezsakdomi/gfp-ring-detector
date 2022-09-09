module Page.Analyze.Msg exposing (..)

import Json.Decode as Decode
import Page.Analyze.Model.Plane exposing (Plane)
import Page.Analyze.Model.Selection as Selection exposing (Scope)
import Page.Analyze.Model.Step as Step
import Page.Analyze.Msg.Helpers as Helpers exposing (MouseEvent, MouseScrollEvent)
import Page.Analyze.WsTypes exposing (..)
import Time

type Msg
   = WsMessage (Result Decode.Error WsMessage)
   | OkWsMessage WsMessage Time.Posix
   | WsClosed WsCloseReason
   | MouseUp
   | ImgEnter Selection.Scope Plane MouseEvent
   | ImgLeave
   | ImgMouseMove Selection.Scope Plane MouseEvent
   | ImgMouseClick Selection.Scope Plane MouseEvent
   | ImgMouseDown Selection.Scope Plane MouseEvent
   | ImgScroll Selection.Scope Plane MouseScrollEvent
   | KeyPress String
   | KeyPressOn String (Maybe Plane, Scope)
