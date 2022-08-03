module Model.Base exposing (..)

type alias Base =
    { secure: Bool
    , host: String
    , port_: Maybe Int
    , path: String
    }

toString base =
    let
        host =
            base.host ++ case base.port_ of
                Nothing -> ""
                Just n -> ":" ++ String.fromInt n
    in
    host ++ base.path

getWsUrl base path = "ws" ++ (if base.secure then "s" else "") ++ "://"
    ++ toString base ++ path

getImgUrl base path = "http" ++ (if base.secure then "s" else "") ++ "://"
    ++ toString base ++ path


