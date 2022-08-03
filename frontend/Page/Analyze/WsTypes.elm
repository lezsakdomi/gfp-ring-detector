module Page.Analyze.WsTypes exposing (..)

import Parser exposing (..)
import Set

type alias WsCloseReason =
    {code: Int, reason: String, wasClean: Bool}

type WsMessage
    = StepStarted {id: Int, name: String, details: Maybe String}
    | Plane {name: String, data: PlaneData}
    | Error {description: String}
    | StepCompleted {id: Int, name: String, durationS: Float, details: Maybe String}

type PlaneData
    = Image {url: String, min: Float, max: Float}
    | List (List String)
    | Unknown String

messageParser : Parser WsMessage
messageParser =
    let
        planeName =
            variable
             { start = Char.isAlpha
             , inner = (\c -> c /= ' ')
             , reserved = Set.empty
             }

        stepName =
            variable
               { start = Char.isAlpha
               , inner = (\c -> Char.isAlphaNum c || c == ' ' || c == '-' || c == '_' )
               , reserved = Set.empty
               }
    in
    oneOf
        [ succeed (\id name details -> StepStarted {id = id, name = name, details = details})
            |. keyword ">"
            |. spaces
            |. keyword "Step"
            |. symbol "#"
            |= int
            |. spaces
            |. symbol "("
            |= stepName
            |. symbol ")"
            |= oneOf
                [ succeed Just
                    |. symbol ", "
                    |= getChompedString (chompWhile (always True))
                , succeed Nothing
                    |. end
                ]
            |. end
        , succeed (\id name duration details -> StepCompleted {id = id, name = name, durationS = duration, details = details})
            |. keyword "COMPLETED"
            |. spaces
            |. keyword "step"
            |. symbol "#"
            |= int
            |. spaces
            |. symbol "("
            |= stepName
            |. symbol "),"
            |. spaces
            |. keyword "took"
            |. spaces
            |= float
            |. spaces
            |. keyword "s"
            |= oneOf
                [ succeed Just
                    |. symbol ", "
                    |= getChompedString (chompWhile (always True))
                , succeed Nothing
                    |. end
                ]
            |. end
        , succeed (\description -> Error {description = description})
            |. keyword "ERROR"
            |. spaces
            |= getChompedString (chompWhile (always True))
        , succeed (\(name, data) -> Plane {data = data, name = name})
            |. keyword "+"
            |. spaces
            |= oneOf
                [ succeed (\name url min max -> (name, Image {url = url, min = min, max = max}) )
                    |. keyword "IMAGE"
                    |. spaces
                    |= planeName
                    |. spaces
                    |= getChompedString (
                        symbol "data:image/"
                            |. variable
                                { start = Char.isLower
                                , inner = Char.isLower
                                , reserved = Set.empty
                                }
                            |. symbol ";base64,"
                            |. let
                                isBase64Char c =
                                    Char.isAlphaNum c || c == '+' || c == '/' || c == '='
                            in chompWhile isBase64Char
                    )
                    |. symbol "#"
                    |= float
                    |. chompWhile (\c -> c == '.')
                    |= float
                    |. end
                , succeed (\name str -> (name, List <| String.split "\n" str))
                    |. keyword "LIST"
                    |. spaces
                    |= planeName
                    |= getChompedString (chompWhile (always True))
                , succeed (\name str -> (name, Unknown str))
                    |. keyword "UNKNOWN"
                    |. spaces
                    |= planeName
                    |. spaces
                    |= getChompedString (chompWhile (always True))
                ]
        ]
    --case String.split " " string of
    --    [] -> Nothing
    --    ">" :: stepIdStr :: stepNameStr :: detailsStrArray ->
    --        case
