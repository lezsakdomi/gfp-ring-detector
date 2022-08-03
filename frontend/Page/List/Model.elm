module Page.List.Model exposing (..)

import PickledData exposing (PickledData)

type alias Model =
    { results: List Item
    , filter: Maybe String
    , loading: Bool
    }

type alias Item =
    { fnameTemplate: String
    , name: String
    , path: String
    , title: String
    , dump: PickledData
    }
