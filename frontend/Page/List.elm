module Page.List exposing (init, update, subscriptions, clientUpdate)

import Browser exposing (Document)
import Constants
import Debug exposing (todo)
import Json.Decode
import Model.Base as Base exposing (Base)
import Page.List.Cmd as ListCmd
import Page.List.Msg exposing (..)
import Page.List.WsTypes exposing (messageDecoder)
import Page.List.Model exposing (..)
import PickledData exposing (PickledData)
import Ports
import Route
import Url

init : Base -> Maybe String -> Route.ListOptions -> (Model, Cmd Msg)
init base dataset {filter} =
    ({results = [], filter = filter, loading = True}, Ports.openWs <| case dataset of
        Nothing -> Base.getWsUrl base "/list"
        Just dataset_ -> Base.getWsUrl base "/list/" ++ Url.percentEncode(dataset_)
    )

clientUpdate : ClientMsg -> Model -> (Model, ListCmd.Cmd)
clientUpdate listClientMsg model =
    case listClientMsg of
        FilterChanged str ->
            (case str of
                "" ->
                    {model | filter = Nothing}

                _ ->
                    {model | filter = Just str}
            , ListCmd.None
            )

        StartAnalysis ->
            (model, ListCmd.StartAnalysis)


update : Msg -> Model -> (Model, ListCmd.Cmd)
update listMsg model =
    case listMsg of
        WsClosed ->
            ({model | loading = False}, ListCmd.None)

        WsMessage (Ok msg) ->
            ({model | results =
                model.results ++ [
                    { fnameTemplate = msg.fnameTemplate
                    , name = msg.name
                    , path = msg.path
                    , title = msg.title
                    , dump = PickledData.fromString msg.dump
                    }]
            }, ListCmd.None)

        WsMessage (Err error) ->
            Debug.log ("Error decoding ws message: " ++ Debug.toString error) (model, ListCmd.None)

        ClientMsg clientMsg ->
            clientUpdate clientMsg model

subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.batch
        [ Ports.wsMessage (Json.Decode.decodeString messageDecoder >> WsMessage)
        , Ports.wsClosed <| always WsClosed
        ]

