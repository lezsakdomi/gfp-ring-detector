module Page.Analyze.Model.Cursor exposing (..)

type alias Cursor =
   { x: Int
   , y: Int
   , zoom: Maybe Float
   }

map2 : Cursor -> (Int -> Int -> (Int, Int)) -> Cursor
map2 cursor f =
    let
        (x, y) =
            f cursor.x cursor.y
    in
    Cursor x y cursor.zoom
