module Route exposing (Route(..), Target(..), ListOptions, Step, Layer, StepLayer(..), Image, Selection, AnalyzeOptions, routeParser, parseRoute, toString)

import Page.Analyze.Model.Cursor exposing (Cursor)
import PickledData exposing (PickledData)
import Url exposing (Url)
import Url.Builder as Builder
import Url.Parser exposing (..)
import Url.Parser.Query as Query

type Target
    = FnameTemplate String
    | EncodedTarget PickledData

type alias ListOptions =
    { filter: Maybe String
    }

type alias StepName = String

type alias Step = StepName

type StepLayer
    = Inputs
    | Outputs

type alias Layer = (Step, StepLayer)

type alias PlaneName = String

type alias Image = (Layer, PlaneName)

type alias Section =
    (StepName, StepLayer)

type alias Scope =
    Maybe (StepName, Maybe StepLayer)

type alias Selection =
    { scope: Scope
    , plane: Maybe PlaneName
    , cursor: Maybe Cursor
    }

type alias AnalyzeOptions =
    { selection: Selection
    --, openLayers: List Layer
    --, openImages: List Image
    , composite: {r: Maybe Image, g: Maybe Image, b: Maybe Image}
    }

type Route
    = List (Maybe String) ListOptions
    | Analyze (Maybe Target) AnalyzeOptions

routeParser : Parser (Route -> a) a
routeParser =
    let
        target str =
            if String.contains "{}" str then
                FnameTemplate str
            else
                EncodedTarget <| PickledData.fromString str
    in
    oneOf
        [ map (List Nothing) (s "list" <?> listOptionsParser)
        , map List (s "list" </> (map Just string) <?> listOptionsParser)
        , map (Analyze Nothing) (s "analyze" <?> analyzeOptionsParser)
        , map Analyze (s "analyze" </> (map (Just << target) string) <?> analyzeOptionsParser)
        ]

listOptionsParser : Query.Parser ListOptions
listOptionsParser =
    Query.map ListOptions (Query.string "filter")

analyzeOptionsParser : Query.Parser AnalyzeOptions
analyzeOptionsParser =
    let
        cursor : Maybe Int -> Maybe Int -> Maybe Float -> Maybe Cursor
        cursor x y z =
            case (x, y, z) of
                (Just x_, Just y_, Nothing) -> Just <| Cursor x_ y_ Nothing
                (Just x_, Just y_, Just z_) -> Just <| Cursor x_ y_ <| Just z_
                _ -> Nothing

        layer : String -> Maybe Layer
        layer str =
            case String.split ":" str of
                [stepName] -> Just (stepName, Outputs)
                [stepName, "in"] -> Just (stepName, Inputs)
                [stepName, "input"] -> Just (stepName, Inputs)
                [stepName, "inputs"] -> Just (stepName, Inputs)
                [stepName, "out"] -> Just (stepName, Outputs)
                [stepName, "output"] -> Just (stepName, Outputs)
                [stepName, "outputs"] -> Just (stepName, Outputs)
                _ -> Nothing

        image : String -> Maybe Image
        image str =
            case String.split ":" str of
                [stepName, "", planeName] -> Just ((stepName, Outputs), planeName)
                [stepName, "in", planeName] -> Just ((stepName, Inputs), planeName)
                [stepName, "input", planeName] -> Just ((stepName, Inputs), planeName)
                [stepName, "inputs", planeName] -> Just ((stepName, Inputs), planeName)
                [stepName, "out", planeName] -> Just ((stepName, Outputs), planeName)
                [stepName, "output", planeName] -> Just ((stepName, Outputs), planeName)
                [stepName, "outputs", planeName] -> Just ((stepName, Outputs), planeName)
                _ -> Nothing

        composite r g b =
            {r = r, g = g, b = b}

        mapAll3 f (a, b, c) =
            (f a, f b, f c)

        uncurry3 f (a, b, c) =
            f a b c

        singletonFilter l =
            case l of
                [item] -> Just item
                _ -> Nothing

        selection cursor_ layers plane =
            let
                layer_ = List.head layers
            in
            Selection (Maybe.map (Tuple.mapSecond Just) layer_) plane cursor_
    in
    Query.map2 AnalyzeOptions
        (Query.map3 selection
            (Query.map3 cursor (Query.int "x") (Query.int "y") (queryFloat "z"))
            (Query.custom "visible" (List.filterMap layer))
            (Query.string "plane")
        )
        --(Query.custom "visible" (List.filterMap layer))
        --(Query.custom "planes" (List.filterMap image))
        (uncurry3 (Query.map3 (composite)) <| mapAll3 (\arg -> Query.custom arg (\l -> singletonFilter l |> Maybe.andThen image)) ("r", "g", "b"))

queryFloat : String -> Query.Parser (Maybe Float)
queryFloat argName =
    let
        f : List String -> Maybe Float
        f l = case l of
            [x] -> String.toFloat x
            _ -> Nothing
    in
    Query.custom argName f

parseRoute : Url -> Maybe Route
parseRoute url =
    parse routeParser url

toString : Builder.Root -> Route -> String
toString root route =
    let
        build : List String -> List Builder.QueryParameter -> Maybe String -> String
        build path params hash =
            --Builder.custom root (Debug.log "path" path) (Debug.log "params" params) (Debug.log "hash" hash)
            Builder.custom root path params hash
    in
    case route of
        List maybeString listOptions ->
            let
                query =
                    case listOptions.filter of
                        Just filter ->
                            [Builder.string "filter" filter]

                        Nothing ->
                            []
            in
            build ["list"] query Nothing

        Analyze maybeTarget analyzeOptions ->
            let
                path =
                    [ Just "analyze"
                    , case maybeTarget of
                        Nothing -> Nothing
                        Just (FnameTemplate tpl) -> Just <| Url.percentEncode tpl
                        Just (EncodedTarget {data}) -> Just <| Url.percentEncode data
                    ]
            in
            build (List.filterMap identity path) [] Nothing
