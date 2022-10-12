module Page.Analyze.WsTypes exposing (..)

import Json.Decode exposing (..)

type alias WsCloseReason =
    {code: Int, reason: String, wasClean: Bool}

type WsMessage
    = StepStarted {id: Int, name: String, details: Maybe String}
    | Plane {name: String, data: PlaneData}
    | Error {description: String}
    | StepCompleted {id: Int, name: String, durationS: Float, details: Maybe String, totalSteps: Int}

type PlaneData
    = Image {url: String, min: Float, max: Float}
    | List (List String)
    | Unknown String

messageParser : Decoder WsMessage
messageParser =
    let
        byType t =
            case t of
                "started" -> stepStarted
                "plane" -> plane
                "error" -> error
                "completed" -> stepCompleted
                s -> fail <| "Unexpected event " ++ s

        stepStarted =
            map3 (\id name details -> StepStarted {id = id, name = name, details = details})
                (field "id" int)
                (field "name" string)
                (maybe <| field "details" string)

        stepCompleted =
            map5 (\id name details duration stepCount -> StepCompleted {id = id, name = name, durationS = duration, details = details, totalSteps = stepCount})
                (field "id" int)
                (field "name" string)
                (maybe <| field "details" string)
                (field "duration" float)
                (field "step_count" int)

        error =
            map (\description -> Error {description = description})
                (field "description" string)

        plane =
            let
                planeDataByType t =
                    case t of
                        Just "image" -> map3 (\url min max -> Image {url = url, min = min, max = max})
                            (field "url" string)
                            (field "min" float)
                            (field "max" float)

                        Just "list" -> map List
                            (field "elements" <| list string)

                        Nothing -> map Unknown
                            (field "data" string)

                        Just s -> fail <| "Unexpected plane type " ++ s
            in
            map2 (\name data -> Plane {data = data, name = name})
                (field "name" string)
                (field "class" string |> maybe |> andThen planeDataByType)

    in
    field "event" string
        |> andThen byType