from os import listdir, path
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import matplotlib.pyplot as plt
import numpy as np
from skimage.io import imread
import os
from keras import utils


def double_conv_block(x, n_filters):
    # Conv2D then ReLU activation
    x = layers.Conv2D(n_filters, 3, padding="same", activation="relu", kernel_initializer="he_normal")(x)
    # Conv2D then ReLU activation
    x = layers.Conv2D(n_filters, 3, padding="same", activation="relu", kernel_initializer="he_normal")(x)
    return x


def downsample_block(x, n_filters):
    f = double_conv_block(x, n_filters)
    p = layers.MaxPool2D(2)(f)
    p = layers.Dropout(0.3)(p)
    return f, p


def upsample_block(x, conv_features, n_filters):
    # upsample
    x = layers.Conv2DTranspose(n_filters, 3, 2, padding="same")(x)
    # concatenate
    x = layers.concatenate([x, conv_features])
    # dropout
    x = layers.Dropout(0.3)(x)
    # Conv2D twice with ReLU activation
    x = double_conv_block(x, n_filters)
    return x


def build_unet_model():
    # inputs
    inputs = layers.Input(shape=(64, 64, 1))
    # encoder: contracting path - downsample
    # 1 - downsample
    f1, p1 = downsample_block(inputs, 32)
    # 2 - downsample
    f2, p2 = downsample_block(p1, 64)
    # 3 - downsample
    f3, p3 = downsample_block(p2, 128)
    # 4 - downsample
    f4, p4 = downsample_block(p3, 256)
    # 5 - bottleneck
    bottleneck = double_conv_block(p4, 512)
    # decoder: expanding path - upsample
    # 6 - upsample
    u6 = upsample_block(bottleneck, f4, 256)
    # 7 - upsample
    u7 = upsample_block(u6, f3, 128)
    # 8 - upsample
    u8 = upsample_block(u7, f2, 64)
    # 9 - upsample
    u9 = upsample_block(u8, f1, 32)
    # outputs
    outputs = layers.Conv2D(3, 1, padding="same", activation="softmax")(u9)
    # unet model with Keras Functional API
    unet_model = tf.keras.Model(inputs, outputs, name="U-Net")
    return unet_model


if __name__ == "__main__":
    import os
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

    unet_model = build_unet_model()
    unet_model.summary()
    utils.plot_model(unet_model)
