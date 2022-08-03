module Page.Analyze.Communication exposing (..)

import Constants
import List.Extra as List
import Page.Analyze.Model as Model exposing (Model)
import Page.Analyze.Model.Cursor exposing (Cursor)
import Page.Analyze.Model.Selection as Selection exposing (Selection)
import Page.Analyze.Model.Step as Step exposing (Step)
import Page.Analyze.Model.WsState as WsState exposing (WsState)
import Page.Analyze.Msg as Msg exposing (Msg)
import Page.Analyze.WsTypes as WsTypes
import Page.Analyze.Model.Plane as Plane exposing (Plane)
import Parser
import Ports
import Task
import Time

update : Msg -> Model -> (Model, Cmd Msg)
update msg model =
    case msg of
        Msg.WsMessage (Err err) ->
            (Debug.log "ws message parse error" (Err err), (model, Cmd.none)) |> Tuple.second

        Msg.WsMessage (Ok wsMsg) ->
            (model, Task.perform (Msg.OkWsMessage wsMsg) Time.now)

        Msg.OkWsMessage wsMsg time ->
            (\steps -> ({model | steps = steps}, Cmd.none)) <|
                let
                    currentSteps = model.steps
                    error errorMessage errorData = Tuple.second (Debug.log errorMessage errorData, currentSteps)
                in
                case wsMsg of
                    WsTypes.StepStarted {id, name, details} ->
                        currentSteps ++ [Step.Ongoing <| Step.Started
                            { definition =
                                { name = name
                                , details = details
                                , inputs = []
                                , outputs = Nothing
                                }
                            , time = time
                            , inputs = []
                            }]

                    WsTypes.Plane plane ->
                        let
                            {name, data} = plane
                        in
                        case List.unconsLast currentSteps of
                            Nothing ->
                                error "Received plane without any step" plane

                            Just (Step.Ongoing (Step.Defined definition), _) ->
                                error "Received plane for a step not even started yet" (definition, plane)

                            Just (Step.Finished (Err fail), _) ->
                                error "Received plane for a failed step" (fail, plane)

                            Just (Step.Ongoing (Step.Started start), steps) ->
                                steps ++ [Step.Ongoing <| Step.Started
                                    { start
                                    | inputs =
                                        start.inputs ++ [Plane name data]
                                    }]

                            Just (Step.Finished (Ok success), steps) ->
                                steps ++ [Step.Finished <| Ok
                                    { success
                                    | outputs =
                                        success.outputs ++ [Plane name data]
                                    }]

                    WsTypes.Error {description} ->
                        case List.unconsLast currentSteps of
                            Nothing ->
                                [Step.Finished <| Err <| Step.Fail Nothing description]

                            Just (Step.Finished _, _) ->
                                currentSteps ++ [Step.Finished <| Err <| Step.Fail Nothing description]

                            Just (Step.Ongoing step, previousSteps) ->
                                previousSteps ++ [Step.Finished <| Err <| Step.Fail (Just step) description]

                    WsTypes.StepCompleted {id, name, durationS, details} ->
                        let
                            newStep : Maybe Step.Ongoing -> Step
                            newStep previous = Step.Finished <| Ok
                                { start =
                                    let
                                        newStart : Maybe Step.Definition -> Step.Start
                                        newStart definition =
                                            { definition =
                                                definition |> Maybe.withDefault
                                                    { name = name
                                                    , details = details
                                                    , inputs = []
                                                    , outputs = Nothing
                                                    }
                                            , time = Time.posixToMillis time - (round <| durationS * 1000) |> Time.millisToPosix
                                            , inputs = []
                                            }
                                    in
                                    case previous of
                                        Nothing ->
                                            newStart Nothing

                                        Just (Step.Defined definition) ->
                                            newStart <| Just definition

                                        Just (Step.Started start) ->
                                            start
                                , time = time
                                , durationS = durationS
                                , outputs = []
                                }
                        in
                        case List.unconsLast currentSteps of
                            Nothing ->
                                [newStep Nothing]

                            Just (Step.Finished _, _) ->
                                currentSteps ++ [newStep Nothing]

                            Just (Step.Ongoing step, previousSteps) ->
                                previousSteps ++ [newStep <| Just step]

        Msg.WsClosed reason ->
            ({model | wsState = WsState.Closed reason}, Cmd.none)

        Msg.ImgEnter scope plane event ->
            let
                {options} = model
                current : Selection
                current = Selection scope (Just plane) Nothing
                dragStarted =
                    (scope, plane, event)
            in
            ({model | options =
                { options
                | current = current
                , dragStarted = Maybe.map (always dragStarted) options.dragStarted
                }
            }, Cmd.none)

        Msg.ImgLeave ->
            let
                {options} = model
            in
            ({model | options =
                { options
                | current = Selection.nothing
                --, dragStarted = Nothing
                }
            }, Cmd.none)

        Msg.ImgMouseMove scope plane event ->
            let
                {options} = model
                {imageView} = options
                cursor : Cursor
                cursor =
                    { x = round <| event.offsetX / options.imageView.zoom - options.imageView.x
                    , y = round <| event.offsetY / options.imageView.zoom - options.imageView.y
                    , zoom = Maybe.andThen (always <| Just options.imageView.zoom) options.public.selection.cursor
                    }
                selection : Selection
                selection = Selection scope (Just plane) (Just cursor)
            in
            ({model | options =
                { options
                | current = selection
                , imageView =
                    case options.dragStarted of
                        Nothing ->
                            imageView

                        Just (scope0, plane0, event0) ->
                            { imageView
                            | x = imageView.x + (event.offsetX - event0.offsetX) / imageView.zoom
                            , y = imageView.y + (event.offsetY - event0.offsetY) / imageView.zoom
                            }
                , dragStarted = Maybe.map (always (scope, plane, event)) options.dragStarted
                }
            }, Cmd.none)

        Msg.ImgMouseClick scope plane event ->
            let
                {options} = model
                {public} = options
                cursor : Cursor
                cursor =
                    { x = round <| event.offsetX / options.imageView.zoom - options.imageView.x
                    , y = round <| event.offsetY / options.imageView.zoom - options.imageView.y
                    --, zoom = Maybe.andThen (always <| Just options.imageView.zoom) options.public.selection.cursor
                    , zoom = Just options.imageView.zoom
                    }
                selection : Selection
                selection = Selection scope (Just plane) <|
                    case public.selection.cursor of
                        Nothing ->
                            Just cursor

                        Just {x, y} ->
                            if x == cursor.x && y == cursor.y then
                                Nothing
                            else
                                Just cursor

            in
            ({model | options =
                { options
                --| current = selection
                | public =
                    { public
                    | selection = Selection.toRouteSelection selection
                    }
                }
            }, Cmd.none)

        Msg.ImgMouseDown scope plane event ->
            let
                {options} = model
            in
            ({model | options =
                { options
                | dragStarted = Just (scope, plane, event)
                }
            }, Cmd.none)

        Msg.MouseUp ->
            let
                {options} = model
                {imageView} = options
            in
            ({model | options =
                { options
                | dragStarted = Nothing
                }
            }, Cmd.none)

        Msg.ImgScroll scope plane event ->
            let
                {options} = model
                {imageView} = options

                newZoom =
                    max Constants.imgZoom.min <| imageView.zoom + event.deltaY * Constants.imgZoom.sensitivity

                newOpts =
                    { options
                    | imageView =
                        { imageView
                        | zoom = newZoom
                        , x = imageView.x - (event.offsetX / imageView.zoom - event.offsetX / newZoom)
                        , y = imageView.y - (event.offsetY / imageView.zoom - event.offsetY / newZoom)
                        , zoomed = True
                        }
                    }
            in
            ( {model | options = newOpts}
            , Cmd.none
            )


subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.batch
        [ Ports.wsMessage (Msg.WsMessage << Parser.run WsTypes.messageParser)
        , Ports.wsClosed (\(code, reason, wasClean) -> Msg.WsClosed {code = code, reason = reason, wasClean = wasClean})
        , Ports.onmouseup (always Msg.MouseUp)
        ]

