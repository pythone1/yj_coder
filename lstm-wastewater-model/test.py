import tensorflow as tf

print("TF version:", tf.__version__)
print("GPU:", tf.config.list_physical_devices('GPU'))

with tf.device('/GPU:0'):
    a = tf.random.normal([2000, 2000])
    b = tf.random.normal([2000, 2000])
    c = tf.matmul(a, b)

print("Done")