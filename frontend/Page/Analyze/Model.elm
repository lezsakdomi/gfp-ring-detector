module Page.Analyze.Model exposing (..)

import Page.Analyze.Model.Cursor exposing (Cursor)
import Page.Analyze.Model.Plane exposing (Plane)
import Page.Analyze.Model.Selection as Selection exposing (Selection)
import Page.Analyze.Model.Step exposing (Step)
import Page.Analyze.Model.WsState exposing (WsState)
import Page.Analyze.Msg.Helpers exposing (MouseEvent)
import Route

type alias Options =
    { public: Route.AnalyzeOptions
    , current: Selection
    , dragStarted: Maybe (Selection.Scope, Plane, MouseEvent)
    , imageView:
        { x: Float
        , y: Float
        , zoom: Float
        , zoomed: Bool
        }
    }

type alias Model =
    { target: Route.Target
    , options: Options
    , steps: List Step
    , wsState: WsState
    }
