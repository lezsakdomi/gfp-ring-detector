module Page.List.View exposing (view, render)

import Browser
import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Maybe.Extra as Maybe
import Page.List.Model as List exposing (..)
import Page.List.Msg exposing (..)
import Page.ListAnalyze.Model as ListAnalyze
import PickledData
import Route
import Url.Builder

view : Model -> Browser.Document Msg
view model =
    let
        mapDocument : (msg -> Msg) -> Browser.Document msg -> Browser.Document Msg
        mapDocument msg doc =
            {title = doc.title, body = List.map (Html.map msg) doc.body}
    in
    mapDocument ClientMsg <| render model Nothing

render : List.Model -> Maybe ListAnalyze.Analysis -> Browser.Document ClientMsg
render {filter, results, loading} currentAnalysis =
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
        , span [] <|
            [ text info
            , text " "
            , a [ href "/dash" ] [ button [] [ text "📊 Open dashboard" ] ]
            ] ++ if not loading && Maybe.isNothing currentAnalysis
                then
                    [ text " ", button [ onClick StartAnalysis ] [ text "▶️ Start analysis on this dataset" ] ]
                else
                    []
        , ul [id "ul"] <|
            List.indexedMap (\index {path, dump, title} ->
                li [] [
                    details [attribute "data-type" "target"]
                        [ summary [] <|
                            (case currentAnalysis of
                                Just {targetIndex, progress} ->
                                    if index == targetIndex
                                        then
                                            [ Html.progress (case progress of
                                                Nothing -> []
                                                Just p -> [value <| String.fromInt p.value, Html.Attributes.max <| String.fromInt p.max]
                                            ) []
                                            , br [] []
                                            , span [ style "width" "1em", style "display" "inline-block" ] []
                                            ]
                                        else
                                            []

                                Nothing ->
                                    []
                            ) ++ [ a
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