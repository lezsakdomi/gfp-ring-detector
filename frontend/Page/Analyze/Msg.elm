module Page.Analyze.Msg exposing (..)

import Page.Analyze.Model.Plane exposing (Plane)
import Page.Analyze.Model.Selection as Selection
import Page.Analyze.Model.Step as Step
import Page.Analyze.Msg.Helpers as Helpers exposing (MouseEvent, MouseScrollEvent)
import Page.Analyze.WsTypes exposing (..)
import Parser exposing (DeadEnd)
import Time

type Msg
   = WsMessage (Result (List DeadEnd) WsMessage)
   | OkWsMessage WsMessage Time.Posix
   | WsClosed WsCloseReason
   | MouseUp
   | ImgEnter Selection.Scope Plane MouseEvent
   | ImgLeave
   | ImgMouseMove Selection.Scope Plane MouseEvent
   | ImgMouseClick Selection.Scope Plane MouseEvent
   | ImgMouseDown Selection.Scope Plane MouseEvent
   | ImgScroll Selection.Scope Plane MouseScrollEvent
