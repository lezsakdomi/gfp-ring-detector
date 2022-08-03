module Page.Analyze.Model.Step exposing (..)

import Page.Analyze.Model.Plane exposing (Plane)
import Time

type alias Definition =
   { name: String
   , details: Maybe String
   , inputs: List String
   , outputs: Maybe (List String)
   }

type alias Start =
   { definition: Definition
   , time: Time.Posix
   , inputs: List Plane
   }

type alias Success =
   { start: Start
   , time: Time.Posix
   , durationS: Float
   , outputs: List Plane
   }

type alias Fail =
   { step: Maybe Ongoing
   , error: String
   }

type Ongoing
    = Defined Definition
    | Started Start

type Step
    = Ongoing Ongoing
    | Finished (Result Fail Success)
