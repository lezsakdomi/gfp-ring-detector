module PickledData exposing (..)

type alias PickledData
    = {data: String, hash: Maybe String}

toString : PickledData -> String
toString dump =
    dump.data ++ (Maybe.map (\str -> ":" ++ str) dump.hash |> Maybe.withDefault "")

fromString : String -> PickledData
fromString string =
    case String.split ":" string of
        [] -> PickledData "" Nothing
        [data] -> PickledData data Nothing
        data :: hash -> PickledData data (Just <| String.join ":" hash)