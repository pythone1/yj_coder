''' This script defines custom metrics and loss functions.

The Adaptive Max-Pool Loss acts as a weighting function that multiplies a
loss value with the maximum loss values within an NxN neighborhood.
An earlier version of this loss function described in:

F. Isikdogan, A.C. Bovik, and P. Passalacqua,
"Learning a River Network Extractor using an Adaptive Loss Function,"
IEEE Geoscience and Remote Sensing Letters, 2018.
'''

import tensorflow as tf
from keras import backend as K
import numpy as np

def running_recall(y_true, y_pred):
    print('y_true',y_true)
    print('y_pred',y_pred)
    TP = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))

    print(TP)

    TP_FN = K.sum(K.round(K.clip(y_true, 0, 1)))

    print(TP_FN)

    recall = TP / (TP_FN + K.epsilon())
    return recall

def running_precision(y_true,y_pred):
    # y_true=tf.cast(y_true, tf.float32)
    # y_pred=tf.cast(y_pred, tf.float32)
    y_true = tf.convert_to_tensor(y_true)
    y_pred = tf.convert_to_tensor(y_pred)
    TP = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    TP_FP = K.sum(K.round(K.clip(y_pred, 0, 1)))
    precision = TP / (TP_FP + K.epsilon())
    return precision

def running_f1(y_true, y_pred):
    precision = running_precision(y_true, y_pred)
    recall = running_recall(y_true, y_pred)
    return 2 * ((precision * recall) / (precision + recall + K.epsilon()))

def adaptive_maxpool_loss(y_true, y_pred, alpha=0.25):
    y_pred = K.clip(y_pred, K.epsilon(), 1. - K.epsilon())
    positive = -y_true * K.log(y_pred) * alpha
    negative = -(1. - y_true) * K.log(1. - y_pred) * (1-alpha)
    pointwise_loss = positive + negative
    max_loss = tf.keras.layers.MaxPool2D(pool_size=8, strides=1, padding='same')(pointwise_loss)
    x = pointwise_loss * max_loss
    x = K.mean(x, axis=-1)
    return x
