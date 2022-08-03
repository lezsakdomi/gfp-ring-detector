module Page.AwaitingTarget exposing (TargetlessPage(..), Model, init, Msg, view, Result(..), update, subscriptions)

import Browser exposing (Document)
import Debug exposing (todo)
import Ports
import Route

type TargetlessPage
    = AnalyzePage Route.AnalyzeOptions

type alias Model =
    { target: String
    , page: TargetlessPage
    }

init : TargetlessPage -> (Model, Cmd Msg)
init page =
    ( Model "" page
    , Ports.showPrompt (Just "Enter a TIF file template with {}-s at channel ID", Nothing)
    )

type Msg
    = PromptResponse (Maybe String)

view : Model -> Document Msg
view {target} =
    Document "" []

type Result
    = SamePage Model
    | DifferentPage Route.Route

update : Msg -> Model -> Result
update msg {page} =
    case (msg, page) of
        (PromptResponse response, AnalyzePage options) ->
            DifferentPage <| Route.Analyze (Maybe.map Route.FnameTemplate response) options

subscriptions : Model -> Sub Msg
subscriptions _ =
    Ports.promptResponse PromptResponse
