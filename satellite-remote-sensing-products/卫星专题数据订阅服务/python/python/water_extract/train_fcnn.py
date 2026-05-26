import os, glob
import argparse
import tensorflow as tf
from metrics_index import running_precision, running_recall, running_f1
import numpy as np
import segmentation_models as sm
import arcticrivermap4
import matplotlib.pyplot as plt
import os

config = tf.compat.v1.ConfigProto()
config.gpu_options.allow_growth = True
session = tf.compat.v1.InteractiveSession(config=config)

class TFModelTrainer:
    def __init__(self, args, data_path):
        self.checkpoint_dir = args.checkpoint_dir
        self.result_path = args.result_path
        # set training parameters
        self.image_size = (1024, 1024)
        self.learning_rate = args.learning_rate  # 0.1
        self.num_epoch = args.num_epoch  # 80
        self.batch_size = args.batch_size  # 4

        # other hyperparameters
        self.data_dim = int(args.data_dim)
        self.model_index = int(args.model_index)

        # create the data generators
        train_filenames = glob.glob(os.path.join(data_path, 'train*.tfrecord*'))
        val_filenames = glob.glob(os.path.join(data_path, 'test*.tfrecord*'))
        print('train_filenames----------------',train_filenames)
        print('val_filenames----------------', val_filenames)

        self.dataset_train = self._data_layer(train_filenames)
        self.dataset_val = self._data_layer(val_filenames)
        print(f'dataset_train --> {self.dataset_train}')
        print(f'dataset_val --> {self.dataset_val}')

        self.dataset_train_size = self._count_TFRecords(train_filenames)
        self.dataset_val_size = self._count_TFRecords(val_filenames)
        print(f'train size --> {self.dataset_train_size}')
        print(f'val size --> {self.dataset_val_size}')

        self.steps_per_epoch = self.dataset_train_size // self.batch_size
        self.validation_steps = self.dataset_val_size // self.batch_size

        print("Training with TensorFlow version", tf.__version__)
        print("Steps per epoch", self.steps_per_epoch, "nr epochs", self.num_epoch, "batch size", self.batch_size)

    def _count_TFRecords(self, filenames):
        return sum(1 for _ in tf.data.TFRecordDataset(filenames))

    def _data_layer(self, filenames, num_threads=48):
        dataset = tf.data.TFRecordDataset(filenames)
        dataset = dataset.map(self._parse_tfrecord, num_parallel_calls=num_threads)
        dataset = dataset.repeat()
        dataset = dataset.batch(self.batch_size, drop_remainder=True)
        dataset = dataset.prefetch(buffer_size=4)
        return dataset

    def _parse_tfrecord(self, example_proto):
        try:
            if self.data_dim == 4:
                keys_to_features = {'B1': tf.io.FixedLenFeature([], tf.string),
                                'B2': tf.io.FixedLenFeature([], tf.string),
                                'B3': tf.io.FixedLenFeature([], tf.string),
                                'B4': tf.io.FixedLenFeature([], tf.string),
                                'L': tf.io.FixedLenFeature([], tf.string)}
                F = tf.io.parse_single_example(serialized=example_proto, features=keys_to_features)
                data = F['B1'], F['B2'], F['B3'], F['B4'], F['L']
        except:
            print('only supports panchromatic or 4band image type')

        image, label = self._decode_images(data)

        return image, label

    def _decode_images(self, data_strings):
        bands = [[]] * len(data_strings)
        for i in range(len(data_strings)):
            bands[i] = tf.image.decode_png(data_strings[i])
        data = tf.concat(bands, -1)
        data = tf.image.random_crop(data, size=[self.image_size[0], self.image_size[1], len(data_strings)])

        data = tf.cast(data, tf.float32)
        image = data[..., :-1] / 255
        label = data[..., -1, None] / 3

        image = self._preprocess_images(image)

        return image, label

    # image processing after random augmentations:
    def _preprocess_images(self, image):
        if self.data_dim == 4:
            image = self._random_channel_mixing(image)
        image = self._gaussian_noise(image)
        image = self._normalize_image(image)
        return image

    def _random_channel_mixing(self, image):
        ccm = tf.eye(4)[None, :, :, None]
        r = tf.random.uniform([3], maxval=0.25) + [0, 1, 0]
        filter = r[None, :, None, None]
        ccm = tf.nn.depthwise_conv2d(input=ccm, filter=filter, strides=[1, 1, 1, 1], padding='SAME', data_format='NHWC')
        ccm = tf.squeeze(ccm)
        image = tf.tensordot(image, ccm, (-1, 0))
        return image

    def _gaussian_noise(self, image):
        r = tf.random.uniform((), maxval=0.04)
        data_dim = self.data_dim
        image = image + tf.random.normal([self.image_size[0], self.image_size[1], data_dim], stddev=r)
        return image

    def _normalize_image(self, image):
        image = tf.cast(image, tf.float32)
        image = image - tf.reduce_min(input_tensor=image)
        image = image / tf.maximum(tf.reduce_max(input_tensor=image), 1)
        return image

    def _optimizer(self):
        optimizer = tf.keras.optimizers.SGD(lr=self.learning_rate, momentum=0.9)
        return optimizer

    def train(self,i):
        # Callbacks
        cp_callback = tf.keras.callbacks.ModelCheckpoint(os.path.join(self.checkpoint_dir,
                                                                      'cp.{epoch:03d}.ckpt'), save_weights_only=True)
        tb_callback = tf.keras.callbacks.TensorBoard(log_dir=self.checkpoint_dir)
        lr_callback = tf.keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5,
                                                           patience=3, verbose=1)
        print('Callbacks is over')

        # Setup training Model
        try:
            if self.model_index == 1 and self.data_dim == 4:
                model = arcticrivermap4.model()
            elif self.model_index == 2:
                model = sm.Unet(backbone_name='resnet18', input_shape=(None, None, self.data_dim),
                                encoder_weights=None, classes=1, activation='sigmoid')
            elif self.model_index == 3:
                model = sm.Unet(backbone_name='resnet34', input_shape=(None, None, self.data_dim),
                                encoder_weights=None, classes=1, activation='sigmoid')
            elif self.model_index == 4:
                model = sm.Linknet(backbone_name='resnet18', input_shape=(None, None, self.data_dim),
                                   encoder_weights=None, classes=1, activation='sigmoid')
            elif self.model_index == 5:
                model = sm.Linknet(backbone_name='resnet34', input_shape=(None, None, self.data_dim),
                                   encoder_weights=None, classes=1, activation='sigmoid')
            print('Setup training Model is over')
        except:
            print('please recheck the supporting neural networks and backbones')
            # model.summary()

        initial_epoch = 0
        # start checkpoints from certain epoch:
        ckpt = tf.train.get_checkpoint_state(self.checkpoint_dir)
        print("self.checkpoint_dir---------------", self.checkpoint_dir)
        if ckpt and ckpt.model_checkpoint_path:
            model.load_weights(ckpt.model_checkpoint_path)
            print("Loaded weights from---------------", ckpt.model_checkpoint_path)
            initial_epoch = int(ckpt.model_checkpoint_path.split('.')[-2])

        '''
        功能：使用model.compile()方法来配置训练方法,
        model.compile(optimizer = 优化器，loss = 损失函数，metrics = ["准确率”])
        '''
        model.compile(optimizer=self._optimizer(),
                      loss=tf.keras.losses.BinaryCrossentropy(),
                      metrics=[tf.keras.metrics.binary_accuracy,
                               running_precision, running_recall, running_f1])

        # 使用model.fit()方法来执行训练过程
        history = model.fit(self.dataset_train,
                            validation_data=self.dataset_val,
                            epochs=self.num_epoch,
                            initial_epoch=initial_epoch,
                            steps_per_epoch=self.steps_per_epoch,
                            validation_steps=self.validation_steps,
                            callbacks=[cp_callback, tb_callback, lr_callback])

        # summarize history for loss
        try:
            plt.plot(history.history['loss'], 'b-')
            plt.plot(history.history['val_loss'], 'b--')
            plt.title('model'+str(self.model_index)+' loss')
            plt.ylabel('loss')
            plt.xlabel('epoch')
            plt.legend(['train', 'test'], loc='upper right')
            fig_name = os.path.join(self.result_path, 'model'+str(self.model_index)+'_loss.png').replace("\\", "/")
            print('fig_name-------------------', fig_name)
            plt.savefig(fig_name)
            plt.close()

            plt.plot(history.history['binary_accuracy'], 'b-')
            plt.plot(history.history['val_binary_accuracy'], 'b--')
            plt.title('model'+str(self.model_index)+'_accuracy')
            plt.ylabel('accuracy')
            plt.xlabel('epoch')
            plt.legend(['train', 'test'], loc='upper right')
            fig_name = os.path.join(self.result_path, 'model' + str(i) + '_accuracy.png').replace("\\", "/")
            print('fig_name-------------------', fig_name)
            plt.savefig(fig_name)
            plt.close()
        except:
            pass

        try:
            # summarize history for precision
            plt.plot(history.history['running_precision'], 'b-')
            plt.plot(history.history['val_running_precision'], 'b--')
            plt.plot(history.history['running_recall'], 'g-')
            plt.plot(history.history['val_running_recall'], 'g--')
            plt.plot(history.history['running_f1'], 'r-')
            plt.plot(history.history['val_running_f1'], 'r--')
            plt.title('model'+str(self.model_index)+f'_precision/recall/f1')
            plt.ylabel('performance')
            plt.xlabel('epoch')
            plt.legend(['precision', 'precision_val', 'recall', 'recall_val',
                        'f1', 'f1_val'], loc='lower right')
            fig_name = os.path.join(self.result_path, 'metrics.png').replace("\\", "/")
            print('history.history--------------------------', history.history)
            print('history.history[running_precision]--------------------------', history.history['running_precision'])
            print('history.history[running_recall]--------------------------', history.history['running_recall'])
            print('history.history[val_running_f1]--------------------------', history.history['val_running_f1'])
            print('fig_name-------------------', fig_name)
            plt.savefig(fig_name)
            plt.close()
        except:
            pass
def main():
    for i in range(5, 6):
        parser = argparse.ArgumentParser()
        file_name = r'H:\Tensorflow\sentinel2_image'
        data_path = os.path.join(file_name, 'tfrecords')
        print('data_path--------------------', data_path)
        models_result_path = os.path.join(file_name, 'model' + str(i))
        print('models_result_path--------------------', models_result_path)
        checkpoint_dir = os.path.join(models_result_path, 'checkpoints')
        print('checkpoint_dir--------------------', checkpoint_dir)
        result_path = os.path.join(models_result_path, 'model_result')
        print('result_path--------------------', result_path)

        parser.add_argument('--data_path', type=str, default=data_path,
                            help="tfrecord文件的路径")
        parser.add_argument('--models_result_path', type=str, default=models_result_path,
                            help="各模型结果的保存路径")
        parser.add_argument('--checkpoint_dir', type=str, default=checkpoint_dir,
                            help="检查点的保存路径")
        parser.add_argument('--result_path', type=str, default=result_path,
                            help="结果图形的保存路径")
        parser.add_argument('--model_index', type=int, default=i,
                            help="FCNN模型的索引，1是DWM，2是U18，3是U34，4是L18，5是L34")
        parser.add_argument('--num_epoch', type=int, default=20,
                            help="训练循环的次数")
        parser.add_argument('--data_dim', type=int, default=4,
                            help="训练数据的维度")
        parser.add_argument('--batch_size', type=int, default=4,
                            help="批量训练的大小")
        parser.add_argument('--learning_rate', type=float, default=0.1,
                            help="训练的学习率")
        args = parser.parse_args()

        if not os.path.exists(args.models_result_path):
            os.mkdir(args.models_result_path)

        if not os.path.exists(args.checkpoint_dir):
            os.mkdir(args.checkpoint_dir)

        if not os.path.exists(args.result_path):
            os.mkdir(args.result_path)
        trainer = TFModelTrainer(args, args.data_path)
        trainer.train(i)

if __name__ == '__main__':
    main()








