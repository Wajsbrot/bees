#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'thiebaut'
__date__ = '02/10/15'

import cPickle
import sys
import numpy as np
import theano

from sklearn.metrics import roc_auc_score

from lasagne.updates import nesterov_momentum
from lasagne.updates import sgd
from lasagne.updates import adam
from lasagne.nonlinearities import linear

from nolearn.lasagne import NeuralNet
from nolearn.lasagne import BatchIterator
from nolearn.lasagne import TrainSplit
from nolearn.lasagne import PrintLayerInfo

from utils import make_submission_file
from utils import regularization_objective
from utils import load_numpy_arrays
from utils import float32
from utils import plot_loss

import lasagne
from lasagne.layers import DenseLayer
from lasagne.layers import InputLayer
from lasagne.layers import DropoutLayer
from lasagne.layers import FeaturePoolLayer
try:
    import lasagne.layers.dnn
    Conv2DLayer = lasagne.layers.dnn.Conv2DDNNLayer
    MaxPool2DLayer = lasagne.layers.dnn.MaxPool2DDNNLayer 
    Pool2DLayer = lasagne.layers.dnn.Pool2DDNNLayer
    print("using CUDNN backend")
except ImportError:
    print("failed to load CUDNN backend")
    try:
        import lasagne.layers.cuda_convnet
        Conv2DLayer = lasagne.layers.cuda_convnet.Conv2DCCLayer
        Pool2DLayer = lasagne.layers.cuda_convnet.Pool2DLayer
        MaxPool2DLayer = lasagne.layers.cuda_convnet.MaxPool2DCCLayer
        print("using CUDAConvNet backend")
    except ImportError as exc:
        print("failed to load CUDAConvNet backend")
        Conv2DLayer = lasagne.layers.conv.Conv2DLayer
        MaxPool2DLayer = lasagne.layers.pool.MaxPool2DLayer
        Pool2DLayer = MaxPool2DLayer
        print("using CPU backend")
from lasagne.nonlinearities import softmax
from lasagne.nonlinearities import LeakyRectify
from lasagne.nonlinearities import rectify
from lasagne.nonlinearities import linear

from adaptative_learning import AdjustVariable
from adaptative_learning import EarlyStopping
from data_augmentation import DataAugmentationBatchIterator
from data_augmentation import FlipBatchIterator
from data_augmentation import ResamplingBatchIterator
from data_augmentation import ResamplingFlipBatchIterator

sys.setrecursionlimit(10000)


def build_layers(name='VGG16', nb_channels=3, crop_size=200, activation_function=rectify):
    """

    :rtype : list
    :param nb_channels: Number of channels per pixels (1 for black and white, 3 for RGB pictures
    :param crop_size: image width and height  after batch data augmentation
    :param activation_function: neurons activation function (same for all)
    :return: model_zoo
    """

    assert isinstance(name, str)

    zoo = {}

    zoo['test'] = [
        (InputLayer, {'shape': (None, nb_channels, crop_size, crop_size)}),

        (Conv2DLayer, {'num_filters': 16, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (DenseLayer, {'num_units': 16}),

        (DenseLayer, {'num_units': 2, 'nonlinearity': softmax}),
    ]

    zoo['reformed-gamblers'] = [
        (InputLayer, {'shape': (None, nb_channels, crop_size, crop_size)}),

        (Conv2DLayer, {'num_filters': 32, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 32, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 32, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 32, 'filter_size': (1, 1), 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 64, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 64, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 128, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 128, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 256, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 256, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),


        (DropoutLayer, {}),
        (DenseLayer, {'num_units': 1024, 'nonlinearity':activation_function}),
        (DenseLayer, {'num_units': 1024, 'nonlinearity':activation_function}),

        (DenseLayer, {'num_units': 2, 'nonlinearity': softmax}),
    ]


    zoo['VGG11'] = [
        (InputLayer, {'shape': (None, nb_channels, crop_size, crop_size)}),

        (Conv2DLayer, {'num_filters': 64, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 128, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 256, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 256, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (DenseLayer, {'num_units': 4096, 'nonlinearity':activation_function}),
        (DropoutLayer, {}),
        (DenseLayer, {'num_units': 4096, 'nonlinearity':activation_function}),
        (DropoutLayer, {}),

        (DenseLayer, {'num_units': 2, 'nonlinearity': softmax}),
    ]

    zoo['VGG11-maxout'] = [
        (InputLayer, {'shape': (None, nb_channels, crop_size, crop_size)}),

        (Conv2DLayer, {'num_filters': 64, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (DropoutLayer, {'p': 0.5}),
        (Conv2DLayer, {'num_filters': 128, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (DropoutLayer, {'p': 0.5}),
        (Conv2DLayer, {'num_filters': 256, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 256, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (DropoutLayer, {'p': 0.5}),
        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (DropoutLayer, {'p': 0.5}),
        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (DropoutLayer, {'p': 0.5}),
        (DenseLayer, {'num_units': 1024, 'nonlinearity': linear}),
        (FeaturePoolLayer, {'pool_size': 2}),
        (DropoutLayer, {'p': 0.5}),
        (DenseLayer, {'num_units': 1024, 'nonlinearity': linear}),
        (FeaturePoolLayer, {'pool_size': 2}),

        (DenseLayer, {'num_units': 2, 'nonlinearity': softmax}),
    ]

    zoo['VGG11-full-maxout'] = [
        (InputLayer, {'shape': (None, nb_channels, crop_size, crop_size)}),

        (Conv2DLayer, {'num_filters': 64, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 128, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 256, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 256, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (DropoutLayer, {'p': 0.5}),
        (DenseLayer, {'num_units': 4096, 'nonlinearity': linear}),
        (FeaturePoolLayer, {'pool_size': 4}),
        (DropoutLayer, {'p': 0.5}),
        (DenseLayer, {'num_units': 4096, 'nonlinearity': linear}),
        (FeaturePoolLayer, {'pool_size': 4}),

        (DenseLayer, {'num_units': 2, 'nonlinearity': softmax}),
    ]


    zoo['MyNet'] = [
        (InputLayer, {'shape': (None, nb_channels, crop_size, crop_size)}),

        (Conv2DLayer, {'num_filters': 64, 'filter_size': 5, 'stride':2, 'pad': 2, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 64, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 128, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 128, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 256, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 256, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 256, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

	(Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (DropoutLayer, {'p': 0.5}),
        (DenseLayer, {'num_units': 4096, 'nonlinearity':activation_function}),
        (FeaturePoolLayer, {'pool_size': 2}),
        (DropoutLayer, {'p': 0.5}),
        (DenseLayer, {'num_units': 4096, 'nonlinearity':activation_function}),
        (FeaturePoolLayer, {'pool_size': 2}),

        (DenseLayer, {'num_units': 2, 'nonlinearity': softmax}),
    ]


    zoo['VGG13'] = [
        (InputLayer, {'shape': (None, nb_channels, crop_size, crop_size)}),

        (Conv2DLayer, {'num_filters': 64, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 64, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 128, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 128, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 256, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 256, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (DenseLayer, {'num_units': 4096, 'nonlinearity':activation_function}),
        (DropoutLayer, {}),
        (DenseLayer, {'num_units': 4096, 'nonlinearity':activation_function}),
        (DropoutLayer, {}),

        (DenseLayer, {'num_units': 2, 'nonlinearity': softmax}),
    ]

    zoo['VGG13-maxout'] = [
        (InputLayer, {'shape': (None, nb_channels, crop_size, crop_size)}),

        (Conv2DLayer, {'num_filters': 64, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 64, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 128, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 128, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 256, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 256, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (DropoutLayer, {}),
        (DenseLayer, {'num_units': 4096, 'nonlinearity':activation_function}),
        (FeaturePoolLayer, {'pool_size': 2}),
        (DropoutLayer, {}),
        (DenseLayer, {'num_units': 4096, 'nonlinearity':activation_function}),
        (FeaturePoolLayer, {'pool_size': 2}),

        (DenseLayer, {'num_units': 2, 'nonlinearity': softmax}),
    ]

    zoo['VGG13-full-maxout'] = [
        (InputLayer, {'shape': (None, nb_channels, crop_size, crop_size)}),

        (Conv2DLayer, {'num_filters': 64, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 64, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 128, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 128, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 256, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 256, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (DropoutLayer, {}),
        (DenseLayer, {'num_units': 4096, 'nonlinearity': linear}),
        (FeaturePoolLayer, {'pool_size': 8}),
        (DropoutLayer, {}),
        (DenseLayer, {'num_units': 4096, 'nonlinearity': linear}),
        (FeaturePoolLayer, {'pool_size': 8}),

        (DenseLayer, {'num_units': 2, 'nonlinearity': softmax}),
    ]



    zoo['VGG16-maxout'] = [
        (InputLayer, {'shape': (None, nb_channels, crop_size, crop_size)}),

        (Conv2DLayer, {'num_filters': 64, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 64, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 128, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 128, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 256, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 256, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 256, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (DropoutLayer, {}),
        (DenseLayer, {'num_units': 1024, 'nonlinearity':activation_function}),
        (FeaturePoolLayer, {'pool_size': 2}),
        (DropoutLayer, {}),
        (DenseLayer, {'num_units': 1024, 'nonlinearity':activation_function}),
        (FeaturePoolLayer, {'pool_size': 2}),

        (DenseLayer, {'num_units': 2, 'nonlinearity': softmax}),
    ]

    zoo['VGG19'] = [
        (InputLayer, {'shape': (None, nb_channels, crop_size, crop_size)}),

        (Conv2DLayer, {'num_filters': 64, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 64, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 128, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 128, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 256, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 256, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 256, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 256, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (DenseLayer, {'num_units': 4096, 'nonlinearity':activation_function}),
        (DropoutLayer, {}),
        (DenseLayer, {'num_units': 4096, 'nonlinearity':activation_function}),
        (DropoutLayer, {}),

        (DenseLayer, {'num_units': 2, 'nonlinearity': softmax}),
    ]

    zoo['VGG19-maxout'] = [
        (InputLayer, {'shape': (None, nb_channels, crop_size, crop_size)}),

        (Conv2DLayer, {'num_filters': 64, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 64, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 128, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 128, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 256, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 256, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 256, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 256, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (DropoutLayer, {}),
        (DenseLayer, {'num_units': 1024, 'nonlinearity':activation_function}),
        (FeaturePoolLayer, {'pool_size': 2}),
        (DropoutLayer, {}),
        (DenseLayer, {'num_units': 1024, 'nonlinearity':activation_function}),
        (FeaturePoolLayer, {'pool_size': 2}),

        (DenseLayer, {'num_units': 2, 'nonlinearity': softmax}),
    ]


    zoo['team_oO'] = [
        (InputLayer, {'shape': (None, nb_channels, crop_size, crop_size)}),

        (Conv2DLayer, {'num_filters': 32, 'filter_size': 5, 'stride': 2, 'pad': 2, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 32, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 64, 'filter_size': 5, 'stride': 2, 'pad': 2, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 64, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 64, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 128, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 128, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 128, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 256, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 256, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 256, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 512, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 2}),

        (DropoutLayer, {}),
        (DenseLayer, {'num_units': 1024, 'nonlinearity':activation_function}),
        (FeaturePoolLayer, {'pool_size': 2}),
        (DenseLayer, {'num_units': 1024, 'nonlinearity':activation_function}),
        (FeaturePoolLayer, {'pool_size': 2}),

        (DenseLayer, {'num_units': 2, 'nonlinearity': softmax}),
    ]

    zoo['AlexNet'] = [
        (InputLayer, {'shape': (None, nb_channels, crop_size, crop_size)}),

        (Conv2DLayer, {'num_filters': 48, 'filter_size': 11, 'stride': 4, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 3, 'stride': 2}),

        (Conv2DLayer, {'num_filters': 128, 'filter_size': 5, 'pad': 2, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 3, 'stride': 2}),

        (Conv2DLayer, {'num_filters': 192, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 192, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (Conv2DLayer, {'num_filters': 128, 'filter_size': 3, 'pad': 1, 'nonlinearity':activation_function}),
        (MaxPool2DLayer, {'pool_size': 3, 'stride': 2}),

        (DenseLayer, {'num_units': 4096, 'nonlinearity':activation_function}),
        (DropoutLayer, {}),
        (DenseLayer, {'num_units': 4096, 'nonlinearity':activation_function}),

        (DenseLayer, {'num_units': 2, 'nonlinearity': softmax}),
    ]

    try:
       layers = zoo[name]
    except KeyError:
        print(name+' not found in available model zoo.')
	exit(1)

    return layers


def auc_roc(y_true, y_prob):
    try:
        return roc_auc_score(y_true, y_prob[:,1])
    except ValueError:
        return 0.

def build_network(verbose=False, **kwargs):
#network_name, data_augmentation='full', lambda2=0.0005, max_epochs=50, nb_channels=3, crop_size=200,
                  #activation_function=rectify, batch_size=48, init_learning_rate=0.01, final_learning_rate=0.0001, dataset_ratio=3.8, final_ratio=2., verbose=False):
    """Build nolearn neural network and returns it

    :param network: pre-defined network name
    :param data_augmentation: type of batch data aug. ('no', 'flip' or 'full')
    :return: NeuralNet nolearn object
    """
    for key,val in kwargs.items():
        exec(key + '=val')
    #data_augmentation = kwargs['data_augmentation']
    if data_augmentation == 'no':
        batch_iterator_train = BatchIterator(batch_size=batch_size)
    elif data_augmentation == 'flip':
        batch_iterator_train = FlipBatchIterator(batch_size=batch_size)
    elif data_augmentation == 'full':
        batch_iterator_train = DataAugmentationBatchIterator(batch_size=batch_size, crop_size=crop_size)
    elif data_augmentation == 'resampling':
        batch_iterator_train = ResamplingBatchIterator(batch_size=batch_size, crop_size=crop_size, scale_delta=scale_delta, max_trans=max_trans, angle_factor=angle_factor,
                                                       max_epochs=max_epochs, dataset_ratio=dataset_ratio, final_ratio=final_ratio)
    elif data_augmentation == 'resampling-flip':
        batch_iterator_train = ResamplingFlipBatchIterator(batch_size=batch_size,
                                                       max_epochs=max_epochs, dataset_ratio=dataset_ratio, final_ratio=final_ratio)
    else:
        raise ValueError(data_augmentation+' is an unknown data augmentation strategy.')

    layers = build_layers(network, nb_channels=nb_channels, crop_size=crop_size,
                          activation_function=activation_function)

    conv_net = NeuralNet(
        layers,

        update=nesterov_momentum,
        update_learning_rate=theano.shared(float32(learning_init)),
        update_momentum=theano.shared(float32(0.9)),
        on_epoch_finished=[
            AdjustVariable('update_learning_rate', start=learning_init, stop=learning_final),
            AdjustVariable('update_momentum', start=0.9, stop=0.999),
            EarlyStopping(patience=patience),
            ],

        batch_iterator_train = batch_iterator_train,
        # batch_iterator_test=DataAugmentationBatchIterator(batch_size=31, crop_size=crop_size),

        objective=regularization_objective,
        objective_lambda2=lambda2,

        train_split=TrainSplit(eval_size=0.1, stratify=True),
        custom_score=('AUC-ROC', auc_roc),
        max_epochs=max_epochs,
        verbose=3,
        )
    if verbose:
        print conv_net.__dict__
    return conv_net
