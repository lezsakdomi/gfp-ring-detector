from os import listdir, path

import numpy as np
import tensorflow as tf
from skimage.io import imread
import os
from model.network import build_unet_model


def augment(input_image, input_mask):
    if tf.random.uniform(()) > 0.5:
        # Random flipping of the image and mask
        input_image = tf.image.flip_left_right(input_image)
        input_mask = tf.image.flip_left_right(input_mask)
    return input_image, input_mask


def normalize(input_image, input_mask):
    input_image = tf.cast(input_image, tf.float32) / 255.0
    input_mask = tf.cast(input_mask, tf.int8) // 32
    # input_mask -= 1 # to range [-1, 1]
    return input_image, input_mask


def load_file(filename, dir):
    image = imread(path.join(basedir, dir, filename), as_gray=True)
    image = image.reshape((64, 64, 1))
    return image


def load_image(filename):
    return load_file(filename, "frames"), load_file(filename, "frame_annotations")


def prepare_image_train(image):
    input_image, input_mask = image
    input_image, input_mask = augment(input_image, input_mask)
    input_image, input_mask = normalize(input_image, input_mask)
    return input_image, input_mask


def prepare_image_test(image):
    input_image, input_mask = image
    input_image, input_mask = normalize(input_image, input_mask)
    return input_image, input_mask


basedir = "."


def main():
    import matplotlib.pyplot as plt

    from model import saved
    try:
        model = saved.get()
    except IOError:
        print("Saved model not found, creating a new one")
        model = build_unet_model()
        model.compile(optimizer=tf.keras.optimizers.Adam(),
                      loss=tf.keras.losses.SparseCategoricalCrossentropy(),
                      metrics="accuracy")

    files = listdir(path.join(basedir, "frame_annotations"))
    images = list(map(load_image, files))
    train_dataset = np.array(list(map(prepare_image_train, images)))
    test_dataset = np.array(list(map(prepare_image_test, images)))

    model_history = model.fit(x=train_dataset[:, 0],
                              y=train_dataset[:, 1],
                              epochs=10,
                              steps_per_epoch=len(images),
                              validation_data=(test_dataset[:, 0], test_dataset[:, 1]))

    saved.save(model)

    return model, model_history.history


if __name__ == "__main__":
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    from matplotlib import pyplot as plt

    model, history = main()

    plt.plot(history['accuracy'])
    plt.plot(history['val_accuracy'])
    plt.title('model accuracy')
    plt.ylabel('accuracy')
    plt.xlabel('epoch')
    plt.legend(['train', 'test'], loc='upper left')
    plt.show()

    plt.plot(history['loss'])
    plt.plot(history['val_loss'])
    plt.title('model loss')
    plt.ylabel('loss')
    plt.xlabel('epoch')
    plt.legend(['train', 'test'], loc='upper left')
    plt.show()
