module Page.Analyze.View exposing (view)

import Browser
import Constants
import Maybe.Extra as Maybe
import Page.Analyze.Model as Model exposing (Model)
import Page.Analyze.Model.Plane exposing (Plane)
import Page.Analyze.Model.Selection as Selection exposing (Section(..))
import Page.Analyze.Model.Step as Step exposing (Step)
import Page.Analyze.Model.WsState as WsState
import Page.Analyze.Msg as Msg exposing (Msg)
import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Page.Analyze.Msg.Helpers exposing (mouseEventDecoder, touchEventDecoder, mouseWheelDecoder, pd)
import Page.Analyze.View.Svg exposing (svg)
import Page.Analyze.View.TargetName as TargetName
import Page.Analyze.WsTypes as WsTypes
import Route

view : Model -> Browser.Document Msg
view model =
    let
        title =
            "GFP-ring-detector | " ++ (TargetName.fromModel model |> Maybe.withDefault "Analyze")

        globalToSvg cursor =
            { x = ((toFloat cursor.x) + model.options.imageView.x + Constants.imgSize.border / model.options.imageView.zoom) -- * model.options.imageView.zoom
            , y = ((toFloat cursor.y) + model.options.imageView.y + Constants.imgSize.border / model.options.imageView.zoom) -- * model.options.imageView.zoom
            }

        imgData_For selector = case selector of
            Nothing -> Nothing
            Just ((stepName, section), planeName) ->
                let
                    extractMatchingUrl plane =
                        if plane.name == planeName then
                            case plane.data of
                                WsTypes.Image imgData -> Just imgData
                                _ -> Nothing
                        else
                            Nothing

                    f step =
                        case (step, section) of
                            (Step.Ongoing (Step.Started {inputs}), Route.Inputs) ->
                                List.filterMap extractMatchingUrl inputs

                            (Step.Finished (Ok success), Route.Inputs) ->
                                List.filterMap extractMatchingUrl success.start.inputs

                            (Step.Finished (Ok success), Route.Outputs) ->
                                List.filterMap extractMatchingUrl success.outputs

                            _ -> []

                in
                case List.concat <| List.map f model.steps of
                    [] -> Nothing
                    imgData :: _ -> Just ((Plane planeName <| WsTypes.Image imgData), imgData)

        renderImg_ imgData_ =
            case imgData_ of
                Just (plane, imgData) -> renderImg model.options Selection.None plane imgData
                Nothing -> img [] []

        redImgData_ = imgData_For model.options.public.composite.r
        greenImgData_ = imgData_For model.options.public.composite.g
        blueImgData_ = imgData_For model.options.public.composite.b
    in
    Browser.Document title
        [ details []
            [ pre [] [ text <| Debug.toString model.options.public ]
            ]
        , ul [id "ul"]
            <| (List.map (renderEntry model.options) <| (List.concat <| List.map transformStep model.steps)
                ++ case model.wsState of
                    WsState.Open ->
                        []

                    WsState.Closed {code} ->
                        [WsClose code]
            )
        , button [] [text "View in 5D Viewer"]
        , svg
            model.options.imageView.zoom
            (Maybe.map globalToSvg <| Maybe.or model.options.current.cursor model.options.public.selection.cursor)
            (Maybe.map globalToSvg <| model.options.public.selection.cursor)
        , details
            ([ id "compositePreview"
            , data "type" "compositePreview"
            ] ++ if List.any (Maybe.isJust) [redImgData_, greenImgData_, blueImgData_]
                then [attribute "open" ""]
                else []
            )
            [ summary [] [text "Composite preview"]
            , div [class "compositeImage"]
                [ div [data "channel" "red"] [renderImg_ redImgData_]
                , div [data "channel" "green"] [renderImg_ greenImgData_]
                , div [data "channel" "blue"] [renderImg_ blueImgData_]
                ]
            ]
        ]

type alias Data =
    {key: String, value: DataValue }

type DataValue
    = DataValueAndExtra String Data
    | DataValueOnly String

type Event
    = StepSection Section
    | Error String

type Entry
    = WsMessage Event
    | WsClose Int

transformStep : Step -> List Entry
transformStep step =
    case step of
        Step.Ongoing ongoingStep ->
            case ongoingStep of
                Step.Defined _  ->
                    []

                Step.Started start ->
                    [ WsMessage <| StepSection <| StepStart start ]

        Step.Finished (Ok success) ->
            let
                {name} = definition
                {definition} = start
                {start, durationS, outputs} = success
            in
            (transformStep <| Step.Ongoing <| Step.Started start) ++ [ WsMessage <| StepSection <| StepSuccess success ]

        Step.Finished (Err fail) ->
            Maybe.withDefault [] (Maybe.map (transformStep << Step.Ongoing) fail.step) ++ [ WsMessage <| Error fail.error ]

renderEntry : Model.Options -> Entry -> Html Msg
renderEntry opts entry =
    let
        liAttrs =
            renderData <| Data "source" <|
                case entry of
                    WsMessage event ->
                        DataValueAndExtra "ws-message" <| Data "event" <|
                            case event of
                                StepSection section ->
                                    let
                                        (eventText, stepText) =
                                            (case section of
                                                StepStart start -> (">", start.definition.name)
                                                StepSuccess success -> ("COMPLETED", success.start.definition.name)
                                            )
                                    in
                                    DataValueAndExtra eventText <| Data "step" <| DataValueOnly stepText

                                Error _ ->
                                    DataValueOnly "event"

                    WsClose _ ->
                        DataValueOnly "ws-close"
        liContent =
            case entry of
                WsClose code ->
                    [span [style "color" "red"] [text <| "Connection closed (code: "++(String.fromInt code)++")"]]

                WsMessage event ->
                    case event of
                        StepSection section ->
                            let
                                {sectionName, definition, planes} =
                                    case section of
                                        StepStart start ->
                                            { sectionName = "inputs"
                                            , definition = start.definition
                                            , planes = start.inputs
                                            }

                                        StepSuccess success ->
                                            { sectionName = "outputs"
                                            , definition = success.start.definition
                                            , planes = success.outputs
                                            }
                            in
                            [ details
                                (liAttrs ++ [data "section" sectionName] ++
                                    case opts.public.selection.scope of
                                        Nothing ->
                                            []

                                        Just (step, maybeLayer) ->
                                            if step == definition.name
                                            then
                                                let
                                                    isSameLayer layer =
                                                        case (section, layer) of
                                                            (StepStart _, Route.Inputs) -> True
                                                            (StepSuccess _, Route.Outputs) -> True
                                                            _ -> False
                                                in
                                                if Maybe.withDefault False <| Maybe.map isSameLayer maybeLayer
                                                then
                                                    [ attribute "open" ""
                                                    , style "background" Constants.colors.selectedSection
                                                    ]
                                                else
                                                    [ style "background" Constants.colors.selectedStep
                                                    ]
                                            else
                                                []
                                )
                                <| [ summary []
                                    (case section of
                                        StepStart _ ->
                                            [ b [] [text definition.name]
                                            , text <| Maybe.withDefault "" definition.details
                                            , button [disabled True] [text "Open in editor"]
                                            , button [disabled True] [text "Open viewer"]
                                            ]

                                        StepSuccess success ->
                                            [ text "COMPLETED "
                                            , b [] [text definition.name]
                                            , text <| " took " ++ (String.fromFloat success.durationS) ++ "s "
                                            , text <| Maybe.withDefault "" definition.details
                                            ]
                                    )
                                ] ++ List.map (renderPlane opts (Selection.Section section)) planes
                            ]

                        Error str ->
                            [pre [] [text str]]
    in
    li liAttrs liContent

renderPlane : Model.Options -> Selection.Scope -> Plane -> Html Msg
renderPlane opts scope plane =
    details
        [ attribute "open" "open"
        , data "source" "ws-message"
        , data "event" "+"
        , data "type" <| case plane.data of
            WsTypes.Image _ -> "IMAGE"
            WsTypes.List _ -> "LIST"
            WsTypes.Unknown _ -> "UNKNOWN"
        , data "plane" plane.name
        ]
        <|
        [ summary [] [ text plane.name ]
        ] ++ case plane.data of
            WsTypes.Unknown str ->
                [ pre [] [text str] ]

            WsTypes.List strings ->
                [ pre [] [text <| String.join "\n" strings] ]

            WsTypes.Image imgData ->
                [ renderImg opts scope plane imgData
                , div [] []
                , div []
                    [ button [ onClick <| Msg.KeyPressOn "r" (Just plane, scope) ] [text "red"]
                    , button [ onClick <| Msg.KeyPressOn "g" (Just plane, scope) ] [text "green"]
                    , button [ onClick <| Msg.KeyPressOn "b" (Just plane, scope) ] [text "blue"]
                    ]
                ]

renderImg opts scope plane {url, min, max} =
    img (
        [ src url
        , data "min-value" <| String.fromFloat min
        , data "max-value" <| String.fromFloat max
        , attribute "loading" "lazy"
        , style "zoom" <| String.fromFloat <| opts.imageView.zoom
        , style "object-position" <| String.join " " <| List.map
            ((\x -> x ++ "px") << String.fromFloat << (\field -> field opts.imageView))
            [ .x, .y ]
        , on "mouseenter" <| mouseEventDecoder <| Msg.ImgEnter scope plane
        , onMouseLeave <| Msg.ImgLeave
        , on "mousemove" <| mouseEventDecoder <| Msg.ImgMouseMove scope plane
        , pd "touchmove" <| touchEventDecoder <| Msg.ImgMouseMove scope plane
        , on "click" <| mouseEventDecoder <| Msg.ImgMouseClick scope plane
        , pd "mousedown" <| mouseEventDecoder <| Msg.ImgMouseDown scope plane
        , pd "touchstart" <| touchEventDecoder <| Msg.ImgMouseDown scope plane
        , pd "mousewheel" <| mouseWheelDecoder <| Msg.ImgScroll scope plane
        , style "image-rendering" "pixelated"
        ] ++ if opts.imageView.zoomed
            then
                [ style "width" <| (String.fromFloat <| Constants.imgSize.width / opts.imageView.zoom) ++ "px"
                , style "height" <| (String.fromFloat <| Constants.imgSize.height / opts.imageView.zoom) ++ "px"
                , style "borderWidth" <| (String.fromFloat <| Constants.imgSize.border / opts.imageView.zoom) ++ "px"
                ]
            else
                [ style "width" <| (String.fromFloat <| Constants.imgSize.width / Constants.imgSize.zoom) ++ "px"
                , style "height" <| (String.fromFloat <| Constants.imgSize.height / Constants.imgSize.zoom) ++ "px"
                ]
        )
        []

renderData : Data -> List (Attribute Msg)
renderData {key, value} =
    case value of
        DataValueAndExtra actualValue extraData ->
            [data key actualValue] ++ renderData extraData

        DataValueOnly actualValue ->
            [data key actualValue]

data k =
    attribute ("data-" ++ k)

