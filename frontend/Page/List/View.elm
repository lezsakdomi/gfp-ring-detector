module Page.List.View exposing (view)

import Browser
import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Page.List.Model exposing (..)
import Page.List.Msg exposing (..)
import PickledData
import Route
import Url.Builder

view : Model -> Browser.Document Msg
view {filter, results, loading} =
    let
        filteredResults =
            case filter of
                Nothing -> results
                Just pattern ->
                    List.filter
                        (\{fnameTemplate} -> String.contains pattern fnameTemplate)
                        results
        info =
            case (loading, filter) of
                (True, _) ->
                    "Discovering targets... " ++ (String.fromInt <| List.length results)
                (_, Nothing) ->
                    "Found " ++ (String.fromInt <| List.length results) ++ " images"
                (_, Just _) ->
                    (String.fromInt <| List.length results) ++ " / " ++
                    (String.fromInt <| List.length filteredResults) ++ " visible " ++
                    "(" ++ (String.fromInt <| round <| toFloat (List.length filteredResults) / toFloat (List.length results) * 100) ++ "%)"

    in
    Browser.Document "GFP Ring Detector | List"
        [ input
            [ placeholder "Search"
            , value (Maybe.withDefault "" filter)
            , onInput FilterChanged
            ] []
        , span [] [ text info ]
        , ul [id "ul"] <|
            List.map (\{path, dump, title} ->
                li [] [
                    details [attribute "data-type" "target"]
                        [ summary []
                            [ a
                                [ href <| Route.toString Url.Builder.Relative <| Route.Analyze
                                    (Just <| Route.EncodedTarget dump)
                                    (Route.AnalyzeOptions (Route.Selection Nothing Nothing Nothing) {r = Nothing, g = Nothing, b = Nothing})
                                ]
                                [ text title
                                ]
                            ]
                        , img
                            [ src <| path ++ "/composite.jpg"
                            , attribute "loading" "lazy"
                            ] []
                        ]
                ]
            ) filteredResults
        ]