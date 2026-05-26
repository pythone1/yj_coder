from segmentation_models import Unet
from segmentation_models import get_preprocessing
import pandas as pd
# prepare data
# train=pd.read_excel('train_dataset11.xlsx')
# test=pd.read_excel('test_dataset11.xlsx')
# x, y=train.iloc[:,-2],train.iloc[:,-1]
#
# preprocessing_fn = get_preprocessing('resnet34')
# x = preprocessing_fn(x)
#
# # prepare model
# model = Unet(backbone_name='resnet34', encoder_weights='imagenet')
# model.compile('Adam', 'binary_crossentropy', ['binary_accuracy'])
#
# # train model
# model.fit(x, y)