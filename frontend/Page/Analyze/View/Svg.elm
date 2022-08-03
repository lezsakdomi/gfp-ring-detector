module Page.Analyze.View.Svg exposing (svg)

import Svg exposing (..)
import Svg.Attributes exposing (..)

svg : Float -> Maybe {x: Float, y: Float} -> Maybe {x: Float, y: Float} -> Svg msg
svg zoom cross marker =
    Svg.svg []
        [ defs []
            [ Svg.filter [id "imgFilter"]
                [ feColorMatrix
                    [ in_ "SourceGraphic"
                    , type_ "matrix"
                    , id "imgFilterCrossV"
                    , result "imgFilterCrossV"
                    , width "1"
                    , x <| String.fromFloat <| Maybe.withDefault -10 <| Maybe.map .x cross
                    , values """
                        -1 0 0 0 1
                        0 -1 0 0 1
                        0 0 -1 0 1
                        0 0 0 1 0
                        """
                    ] []
                , feColorMatrix
                    [ in_ "SourceGraphic"
                    , type_ "matrix"
                    , id "imgFilterCrossH"
                    , result "imgFilterCrossH"
                    , height "1"
                    , y <| String.fromFloat <| Maybe.withDefault -10 <| Maybe.map .y cross
                    , values """
                        -1 0 0 0 1
                        0 -1 0 0 1
                        0 0 -1 0 1
                        0 0 0 1 0
                        """
                    ] []
                , feColorMatrix
                    [ in_ "SourceGraphic"
                    , type_ "matrix"
                    , id "imgFilterDefCross"
                    , result "imgFilterDefCross"
                    , width "1", height "1"
                    , x <| String.fromFloat <| Maybe.withDefault 0 <| Maybe.map .x marker
                    , y <| String.fromFloat <| Maybe.withDefault 0 <| Maybe.map .y marker
                    , values """
                        -1 0 0 0 1
                        0 -1 0 0 1
                        0 0 -1 0 1
                        0 0 0 1 0
                        """
                    ] []
                , feMerge [] []
                , feMerge []
                    [ feMergeNode [in_ "SourceGraphic"] []
                    , feMergeNode [in_ "imgFilterCrossV"] []
                    , feMergeNode [in_ "imgFilterCrossH"] []
                    , feMergeNode [in_ "imgFilterDefCross"] []
                    ]
                ]
            ]
        ]

