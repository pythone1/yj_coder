''' Creates tfrecords given GeoTIFF files.
We provide a copy of the dataset in tfrecords format.
You should not need this script unless you modify the dataset.
'''
import os, glob
import argparse
import random
import math
import numpy as np
import tifffile as tiff
# import tensorflow as tf
import tensorflow.compat.v1 as tf# 可以用于从TensorFlow 1.x到2.x的复杂迁移项目的程序开头
tf.disable_eager_execution()
import imgProcess as imgpro

import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

def _bytes_feature(value):
    return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))

def _create_tfexample(B1, B2, B3, B4, label):
    example = tf.train.Example(features=tf.train.Features(feature={
            'B1': _bytes_feature(B1),
            'B2': _bytes_feature(B2),
            'B3': _bytes_feature(B3),
            'B4': _bytes_feature(B4),
            'L': _bytes_feature(label)
            }))
    return example

def preprocess_and_encode_sample(data_tensor):
    image = data_tensor[..., :-1]
    label = data_tensor[..., -1]
    print('label--------------', label)
    print('image--------------', image)

    image = tf.cast(image, tf.float32)
    image = image - tf.reduce_min(image)
    image = image / tf.maximum(tf.reduce_max(image), 1)
    image = image * 255

    image = tf.cast(image, tf.uint8)
    label = tf.cast(label, tf.uint8)


    #encode_png图片解码函数
    B1 = tf.image.encode_png(image[..., 0, None])
    B2 = tf.image.encode_png(image[..., 1, None])
    B3 = tf.image.encode_png(image[..., 2, None])
    B4 = tf.image.encode_png(image[..., 3, None])
    L = tf.image.encode_png(label[..., None])
    return [B1, B2, B3, B4, L]

def create_tfrecords(save_dir, dataset_name, filenames, images_per_shard):
    tf.compat.v1.disable_eager_execution()
    data_placeholder = tf.compat.v1.placeholder(tf.uint16) #tf.compat.v1.placeholder是占位符,相当于定义了一个变量,提前分配了需要的内存。
    processed_bands = preprocess_and_encode_sample(data_placeholder)

    with tf.compat.v1.Session() as sess:
        num_shards = math.ceil(len(filenames) / images_per_shard)
        for shard in range(num_shards):
            output_filename = os.path.join(save_dir, '{}_{:03d}-of-{:03d}.tfrecord'
                                        .format(dataset_name, shard, num_shards))
            print('Writing into {}'.format(output_filename))

            output_filename=output_filename.replace("\\", "/")
            print('output_filename---------------',output_filename)

            filenames_shard = filenames[shard*images_per_shard:(shard+1)*images_per_shard]


            with tf.io.TFRecordWriter(output_filename) as tfrecord_writer:
                for filename in filenames_shard:
                    data = tiff.imread(filename)

                    B1, B2, B3, B4, L = sess.run(processed_bands, feed_dict={data_placeholder: data})

                    example = _create_tfexample(B1, B2, B3, B4, L)


                    tfrecord_writer.write(example.SerializeToString())

    print('Finished writing {} images into TFRecords'.format(len(filenames)))

def main(args):
    filenames=[]
    os.chdir(args.input_dir)

    tiffiles = glob.glob('*.tif')
    for tiffile in enumerate(tiffiles):
        filename = os.path.join(args.input_dir, str(tiffile[1])).replace("\\", "/")
        filenames.append(filename)
    print('filenames----------', filenames)

    random.seed(args.seed)
    random.shuffle(filenames)

    num_test = args.num_test_images

    # create TFRecords for the training and test sets
    create_tfrecords(save_dir=args.output_dir,
                     dataset_name='train',
                     filenames=filenames[num_test:],
                     images_per_shard=args.images_per_shard)
    create_tfrecords(save_dir=args.output_dir,
                     dataset_name='test',
                     filenames=filenames[:num_test],
                     images_per_shard=args.images_per_shard)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--input_dir', type=str, default=r'H:\Tensorflow\sentinel2_image\addlabel_image',
                        help='读取tif文件到地址')
    parser.add_argument('--output_dir', type=str, default=r'H:\Tensorflow\sentinel2_image\addlabel_image\tfrecords',
                        help='输出TFRecords文件到保存地址')
    parser.add_argument('--images_per_shard', type=int, default=300,
                        help='每个tfrecord文件存储的tif影像数量')
    parser.add_argument('--num_test_images', type=float, default=400,
                        help='模型训练中测试tif影像的数量')
    parser.add_argument('--seed', type=int, default=42,
                        help='可重复训练、测试拆分的随机种子数量')
    args = parser.parse_args()
    if not os.path.exists(args.output_dir):
        os.mkdir(args.output_dir)
    main(args)