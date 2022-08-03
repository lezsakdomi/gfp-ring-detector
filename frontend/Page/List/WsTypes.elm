module Page.List.WsTypes exposing (WsMessage, messageDecoder)

--            {
--                'fnameTemplate': image.fname_template,
--                'name': image.name,
--                'path': image.path,
--                'title': str(image),
--                'stats': image.stats,
--                'dump': codecs.encode(pickle.dumps(image), 'base64').decode(),
--            }

import Dict exposing (Dict)
import Json.Decode exposing (..)

type alias WsMessage =
    { fnameTemplate: String
    , name: String
    , path: String
    , title: String
    , stats: Maybe (Dict String String)
    , dump: String
    }

messageDecoder : Decoder WsMessage
messageDecoder =
    map6 WsMessage
        (field "fnameTemplate" string)
        (field "name" string)
        (field "path" string)
        (field "title" string)
        (field "stats" <| oneOf
            [ map Just <| dict string
            , null Nothing
            ]
        )
        (field "dump" string)