module Model exposing (..)

import Browser.Navigation as Nav
import Model.Base exposing (Base)
import Page.Analyze
import Page.AwaitingTarget
import Page.List.Model
import Page.ListAnalyze.Model

type PageModel
    = AnalyzeModel Page.Analyze.Model
    | ListModel Page.List.Model.Model
    | ListAnalyzeModel Page.ListAnalyze.Model.Model
    | AwaitingTargetModel Page.AwaitingTarget.Model

type alias Model =
    { key: Nav.Key
    , pageModel: PageModel
    , jsInitialized: Bool
    , base: Base
    }
