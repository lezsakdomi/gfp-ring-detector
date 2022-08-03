module Constants exposing (..)

imgSize =
    { width = 1388 * imgZoom.default
    , height = 1040 * imgZoom.default
    , zoom = imgZoom.default
    , border = 5.0
    }

imgZoom =
    { default = 0.25
    , min = 0.1
    , sensitivity = -0.01
    }

colors =
    { selectedStep = "rgba(0, 0, 64, 0.75)"
    , selectedSection = "rgba(16, 16, 128, 0.5)"
    , selectedPlane = "rgba(64, 64, 128, 0.5)"
    }
