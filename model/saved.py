from os import path

import keras.models

filename = path.join(path.dirname(__file__), "SavedModel")
loaded_model: keras.Model = None


def get():
    global loaded_model
    if loaded_model is None:
        loaded_model = keras.models.load_model(filename)

    return loaded_model


def save(new_model=None):
    global loaded_model

    if new_model is not None:
        loaded_model = new_model

    loaded_model.save(filename)
