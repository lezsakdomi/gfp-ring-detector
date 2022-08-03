module Main exposing (main)

import Browser exposing (Document, UrlRequest)
import Browser.Navigation as Nav
import Debug exposing (todo)
import Html
import Model exposing (Model)
import Model.Base exposing (Base)
import Page.Analyze
import Page.AwaitingTarget
import Page.List
import Page.List.Msg
import Page.List.View
import Ports
import Route
import Url exposing (Url)

type alias Flags = ()

type Msg
    = UrlChange Url
    | UrlRequest UrlRequest
    | PageMsg PageMsg
    | JsInitialized ()

type PageMsg
    = AwaitingTargetMsg Page.AwaitingTarget.Msg
    | AnalyzeMsg Page.Analyze.Msg
    | ListMsg Page.List.Msg.Msg

main =
    Browser.application
        { init = init
        , view = view
        , update = update
        , subscriptions = subscriptions
        , onUrlRequest = UrlRequest
        , onUrlChange = UrlChange
        }

init : Flags -> Url -> Nav.Key -> ( Model, Cmd Msg )
init _ url key =
    let
        base =
            { secure = case url.protocol of
                Url.Http -> False
                Url.Https -> True
            , host = url.host
            , port_ = url.port_
            , path = ""
            }
    in
    Tuple.mapBoth
        (\pageModel ->
            { key = key
            , pageModel = pageModel
            , jsInitialized = False
            , base = base
            }
        )
        (Cmd.map PageMsg)
        (initPage base <| Maybe.withDefault (Route.List Nothing <| Route.ListOptions Nothing) <| Route.parseRoute url)


pageResultToMainResult mainModel =
    Tuple.mapBoth
        (\model -> {mainModel | pageModel = model})
        (Cmd.map PageMsg)


initPage : Base -> Route.Route -> (Model.PageModel, Cmd PageMsg)
initPage base route =
    case route of
        Route.List dataset listOptions ->
            Page.List.init base dataset listOptions
                |> Tuple.mapBoth
                    Model.ListModel
                    (Cmd.map ListMsg)
        Route.Analyze Nothing analyzeOptions ->
            Page.AwaitingTarget.init (Page.AwaitingTarget.AnalyzePage analyzeOptions)
                |> Tuple.mapBoth
                    Model.AwaitingTargetModel
                    (Cmd.map AwaitingTargetMsg)
        Route.Analyze (Just target) analyzeOptions ->
            Page.Analyze.init base target analyzeOptions
                |> Tuple.mapBoth
                    Model.AnalyzeModel
                    (Cmd.map AnalyzeMsg)


view : Model -> Document Msg
view {pageModel, base} =
    let
        mapDocument : (msg -> Msg) -> Document msg -> Document Msg
        mapDocument msg doc =
            {title = doc.title, body = List.map (Html.map msg) doc.body}
    in
    case pageModel of
        Model.AwaitingTargetModel model ->
            mapDocument (PageMsg << AwaitingTargetMsg) <| Page.AwaitingTarget.view model

        Model.AnalyzeModel model ->
            mapDocument (PageMsg << AnalyzeMsg) <| Page.Analyze.view model

        Model.ListModel model ->
            mapDocument (PageMsg << ListMsg) <| Page.List.View.view model

update : Msg -> Model -> ( Model, Cmd Msg )
update mainMsg mainModel =
    let
        {pageModel, key, base} = mainModel

        pageResult = pageResultToMainResult mainModel
    in
    case (mainMsg, pageModel) of
        (UrlRequest (Browser.Internal url), _) ->
            init () url key
                |> Tuple.mapSecond
                    (\cmd -> Cmd.batch
                        [ Ports.closeWs ()
                        , cmd
                        , Nav.pushUrl key <| Url.toString url
                        ]
                    )

        (UrlRequest (Browser.External url), _) ->
            (mainModel, Nav.load url)

        (UrlChange _, _) ->
            (mainModel, Cmd.none)

        (PageMsg pageMsg, _) ->
            let
                updateModel container model =
                    {mainModel | pageModel = container model}
            in
            case (pageMsg, pageModel) of
                (AwaitingTargetMsg msg, Model.AwaitingTargetModel model) ->
                    case Page.AwaitingTarget.update msg model of
                        Page.AwaitingTarget.SamePage newModel ->
                            (updateModel Model.AwaitingTargetModel newModel, Cmd.none)

                        Page.AwaitingTarget.DifferentPage route ->
                            pageResult <| initPage base route

                (AwaitingTargetMsg _, _) ->
                    todo "Unexpected msg/model combo"

                (AnalyzeMsg msg, Model.AnalyzeModel model) ->
                    pageResult <| (Page.Analyze.update msg model |> Tuple.mapBoth Model.AnalyzeModel (Cmd.map AnalyzeMsg))

                (AnalyzeMsg _, _) ->
                    todo "Unexpected msg/model combo"

                (ListMsg msg, Model.ListModel model) ->
                    pageResult <| (Model.ListModel <| Page.List.update msg model, Cmd.none)

                (ListMsg _, _) ->
                    todo "Unexpected msg/model combo"

        (JsInitialized (), _) ->
            ({mainModel | jsInitialized = True}, Cmd.none)

subscriptions : Model -> Sub Msg
subscriptions {pageModel} =
    Sub.batch
    [ case pageModel of
        Model.AwaitingTargetModel model ->
            Sub.map (PageMsg << AwaitingTargetMsg) <| Page.AwaitingTarget.subscriptions model

        Model.AnalyzeModel model ->
            Sub.map (PageMsg << AnalyzeMsg) <| Page.Analyze.subscriptions model

        Model.ListModel model ->
            Sub.map (PageMsg << ListMsg) <| Page.List.subscriptions model
    , Ports.initialized JsInitialized
    ]
