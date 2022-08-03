module Page.Analyze exposing (Model, init, Msg, update, view, subscriptions)

import Constants
import Model.Base as Base exposing (Base)
import Page.Analyze.Communication
import Page.Analyze.Model as Model exposing (Model)
import Page.Analyze.Model.Selection as Selection
import Page.Analyze.Model.WsState as WsState
import Page.Analyze.Msg as Msg exposing (Msg)
import Page.Analyze.View
import Page.Analyze.Model.Cursor exposing (Cursor)
import PickledData
import Ports
import Route

type alias Model =
   Model.Model

init : Base -> Route.Target -> Route.AnalyzeOptions -> (Model, Cmd Msg)
init base target options =
    let
        getWsUrl path =
            Base.getWsUrl base <| "/analyze/" ++ path
    in
    (
        { target = target
        , options = Model.Options options Selection.nothing Nothing <|
            { x = 0.0
            , y = 0.0
            , zoom = Constants.imgSize.zoom
            , zoomed = False
            }
        , steps = []
        , wsState = WsState.Open
        }
    , Ports.openWs <| case target of
        Route.FnameTemplate tpl -> getWsUrl tpl
        Route.EncodedTarget data -> getWsUrl <| PickledData.toString data
    )

type alias Msg =
   Msg.Msg

update = Page.Analyze.Communication.update

view = Page.Analyze.View.view

subscriptions = Page.Analyze.Communication.subscriptions
