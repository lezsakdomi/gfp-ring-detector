module Page.Analyze.View.TargetName exposing (..)

import Maybe.Extra as Maybe
import Page.Analyze.Model exposing (Model)
import Page.Analyze.Model.Plane exposing (Plane)
import Page.Analyze.Model.Step as Step exposing (Step)
import Page.Analyze.WsTypes as WsTypes
import Route

fromPlane : Plane -> Maybe String
fromPlane plane =
    if plane.name == "target" then
        case plane.data of
            WsTypes.Unknown str ->
                Just str

            _ ->
                Nothing
    else
        Nothing

fromPlanes : List Plane -> Maybe String
fromPlanes =
    List.filterMap fromPlane >> List.head

fromOngoingStep : Step.Ongoing -> Maybe String
fromOngoingStep ongoingStep =
    case ongoingStep of
        Step.Defined _ ->
            Nothing

        Step.Started {inputs} ->
            fromPlanes inputs

fromStep : Step -> Maybe String
fromStep step =
    case step of
        Step.Ongoing ongoing ->
            fromOngoingStep ongoing

        Step.Finished (Ok ({start, outputs})) ->
            fromPlanes start.inputs |> Maybe.or (fromPlanes outputs)

        Step.Finished (Err fail) ->
            fail.step |> Maybe.andThen fromOngoingStep

fromModel : Model -> Maybe String
fromModel model =
    case model.target of
        Route.FnameTemplate tpl ->
             Just tpl

        Route.EncodedTarget _ ->
            List.head <| List.filterMap fromStep model.steps
