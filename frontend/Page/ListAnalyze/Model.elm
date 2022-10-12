module Page.ListAnalyze.Model exposing (..)

import Model.Base exposing (Base)
import Page.List.Model as List

type alias Model =
   { base: Base
   , listModel: List.Model
   , currentAnalysis: Maybe Analysis
   }

type alias Analysis =
   { targetIndex: Int
   , progress: Maybe {value: Int, max: Int}
   }
