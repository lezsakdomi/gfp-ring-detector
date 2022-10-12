module Page.ListAnalyze exposing (init, view, subscriptions, update)

import Browser exposing (Document)
import Html
import Json.Decode exposing (decodeString)
import List.Extra as List
import Model.Base exposing (Base)
import Page.Analyze as Analyze
import Page.Analyze.Msg as AnalyzeMsg
import Page.Analyze.WsTypes as WsTypes exposing (WsMessage(..))
import Page.List
import Page.List.Cmd as ListCmd
import Page.List.Model as List
import Page.List.View as List
import Page.ListAnalyze.Model as Model exposing (Model)
import Page.ListAnalyze.Msg as Msg exposing (Msg)
import Ports
import Route

init : Base -> List.Model -> (Model, Cmd Msg)
init base listModel =
    startAnalysis base listModel 0


startAnalysis : Base -> List.Model -> Int -> (Model, Cmd Msg)
startAnalysis base listModel i =
    case List.getAt i listModel.results of
        Just item ->
            (Model base listModel <| Just <| Model.Analysis i Nothing, Cmd.batch
                [ Ports.closeWs ()
                , Analyze.openWs base <| Route.EncodedTarget item.dump
                ])

        Nothing ->
            (Model base listModel Nothing, Cmd.none)

view : Model -> Document Msg
view {base, listModel, currentAnalysis} =
    let
        mapDocument : (msg -> Msg) -> Browser.Document msg -> Browser.Document Msg
        mapDocument msg doc =
            {title = doc.title, body = List.map (Html.map msg) doc.body}
    in
    mapDocument Msg.ClientMsg <| List.render listModel currentAnalysis

subscriptions : Model -> Sub Msg
subscriptions _ =
    Sub.batch
        [ Ports.wsMessage (Msg.WsMessage << decodeString WsTypes.messageParser)
        , Ports.wsClosed (\(code, reason, wasClean) -> Msg.WsClosed {code = code, reason = reason, wasClean = wasClean})
        ]

update : Msg -> Model -> (Model, Cmd Msg)
update msg model =
    let
        {currentAnalysis, listModel, base} =
            model
    in
    case msg of
        Msg.ClientMsg clientMsg ->
            ({model | listModel = case Page.List.clientUpdate clientMsg model.listModel of
                (listModel_, ListCmd.None) ->
                    listModel_

                (_, ListCmd.StartAnalysis) ->
                    Debug.todo "This should not happen"
            }, Cmd.none)

        Msg.WsMessage (Err err) ->
            (Debug.log "ws message parse error" (Err err), (model, Cmd.none)) |> Tuple.second

        Msg.WsMessage (Ok data) ->
            case currentAnalysis of
                Just {progress, targetIndex} ->
                    case data of
                        StepCompleted {id, totalSteps} ->
                            if id == totalSteps - 1
                                then
                                    startAnalysis base listModel <| targetIndex + 1
                                else
                                    ({model | currentAnalysis = Just <| Model.Analysis targetIndex <| Just {value = id + 1, max = totalSteps}}, Cmd.none)

                        _ -> (model, Cmd.none)

                Nothing ->
                    (model, Cmd.none)

        Msg.WsClosed wsCloseReason ->
            case currentAnalysis of
                Just {targetIndex} ->
                    startAnalysis base listModel <| targetIndex + 1

                Nothing ->
                    (model, Cmd.none)
