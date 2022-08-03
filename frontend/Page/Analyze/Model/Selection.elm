module Page.Analyze.Model.Selection exposing (..)

import Page.Analyze.Model.Cursor exposing (Cursor)
import Page.Analyze.Model.Plane exposing (Plane)
import Page.Analyze.Model.Step exposing (..)
import Route

type Section
    = StepStart Start
    | StepSuccess Success

type Scope
    = Step Definition
    | Section Section
    | None

type alias Selection =
    { scope: Scope
    , plane: Maybe Plane
    , cursor: Maybe Cursor
    }

nothing =
    Selection None Nothing Nothing

map selection scope plane cursor =
    Selection
        (scope selection.scope)
        (plane selection.plane)
        (cursor selection.cursor)

withScope scope selection =
    map selection (always scope) identity identity

mapPlane plane selection =
    map selection identity plane identity

mapCursor cursor selection =
    map selection identity identity cursor

toRouteSelection : Selection -> Route.Selection
toRouteSelection {scope, plane, cursor} =
    { scope = case scope of
        None ->
            Nothing

        Step definition ->
            Just (definition.name, Nothing)

        Section section ->
            case section of
                StepStart start ->
                    Just (start.definition.name, Just Route.Inputs)

                StepSuccess success ->
                    Just (success.start.definition.name, Just Route.Outputs)

    , plane = Maybe.map .name plane
    , cursor = cursor
    }
