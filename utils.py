#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'thiebaut'
__date__ = '01/10/15'

import os
import matplotlib.pyplot as plt
import numpy as np
from datetime import date
import pandas as pd

from PIL import Image
from nolearn.lasagne import objective
from lasagne.layers import get_all_params
from skimage.transform import AffineTransform
from skimage.transform import warp
from skimage.util import pad
from math import pi


def float32(k):
    return np.cast['float32'](k)


def show_img(img_id, root='data/images', test=False):
    dir = 'test' if test else 'train'
    path = os.path.join(root, dir, '{}.jpg'.format(img_id))
    im = Image.open(path)
    im_np = np.array(im)
    plt.imshow(im_np)


def print_predictions(predictions):
    values, counts = np.unique(predictions, return_counts=True)
    for v, c in zip(values, counts):
        print 'Number of {}: {}'.format(v, c)


def get_image(path, img_id, n_channels=3, width=None):
    """
    Get pixels values from image id
    :param img_id: image id (int)
    :return: numpy flattened array with integer pixels values (np.uint8 array)
    """
    filename = "{}.jpg".format(img_id)
    filepath = os.path.join(path, filename)
    pixels = np.array(Image.open(filepath), dtype=np.uint8)
    if pixels.shape[2] > n_channels:
        # raise Warning('Warning: Image ' + str(img_id) + ' is RGBA (alpha), converting to RGB.')
        pixels = pixels[:, :, :n_channels]
    if width is not None:
        pixels = pixels[:width, :width, :]
    return pixels.flatten()


def make_submission_file(predictions, images_id, output_filepath="submission_" + str(date.today()) + ".csv"):
    predictions_df = pd.DataFrame(predictions[:, 1], index=images_id, columns=['genus'])
    predictions_df.index.names = ['id']
    predictions_df.to_csv(output_filepath)


def load_numpy_arrays(filename):
    f = open(filename, 'rb')
    data = np.load(f)
    return np.array(data['arr_0']).astype(np.float32), np.array(data['arr_1']).astype(np.int32), data['arr_2']


def regularization_objective(layers, lambda1=0., lambda2=0., *args, **kwargs):
    # default loss
    losses = objective(layers, *args, **kwargs)
    # get the layers' weights, but only those that should be regularized
    # (i.e. not the biases)
    weights = get_all_params(layers[-1], regularizable=True)
    # sum of absolute weights for L1
    sum_abs_weights = sum([abs(w).sum() for w in weights])
    # sum of squared weights for L2
    sum_squared_weights = sum([(w ** 2).sum() for w in weights])
    # add weights to regular loss
    losses += lambda1 * sum_abs_weights + lambda2 * sum_squared_weights
    return losses


def plot_loss(net, filename="submissions/loss_" + str(date.today()) + ".png", show=False):
    train_loss = np.array([i["train_loss"] for i in net.train_history_])
    valid_loss = np.array([i["valid_loss"] for i in net.train_history_])
    plt.plot(train_loss, linewidth=3, label="train")
    plt.plot(valid_loss, linewidth=3, label="valid")
    plt.grid()
    plt.legend()
    plt.xlabel("epoch")
    plt.ylabel("loss")
    # plt.ylim(1e-3, 1e-2)
    plt.yscale("log")
    plt.savefig(filename)
    if show:
        plt.show()


def plot_conv_weights(layer, filename, figsize=(6, 6)):
    """Plot the weights of a specific layer.
    Only really makes sense with convolutional layers.
    Parameters
    ----------
    layer : lasagne.layers.Layer
    """
    W = layer.W.get_value()
    shape = W.shape
    nrows = np.ceil(np.sqrt(shape[0])).astype(int)
    ncols = nrows

    for feature_map in range(shape[1]):
        figs, axes = plt.subplots(nrows, ncols, figsize=figsize)

        for ax in axes.flatten():
            ax.set_xticks([])
            ax.set_yticks([])
            ax.axis('off')

        for i, (r, c) in enumerate(product(range(nrows), range(ncols))):
            if i >= shape[0]:
                break
            axes[r, c].imshow(W[i, feature_map], cmap='gray',
                              interpolation='nearest')
    plt.savefig(filename)


def data_augmentation_test(img_id=1, crop_size=200, pad_size=100):
    Xb = np.array(Image.open('data/images/train/' + str(img_id) + '.jpg'), dtype=np.uint8) / np.float32(255.)

    im_size = Xb.shape[0]
    frame_size = im_size + 2 * pad_size
    print "X shape ", Xb.shape
    padded = np.zeros((3, frame_size, frame_size))
    for i in range(3):
        padded[i] = pad(np.swapaxes(Xb, 0, 2)[i], (pad_size, pad_size), 'reflect')
    padded = np.swapaxes(padded, 0, 2)
    print "Padded shape ", padded.shape

    lower_cut = (im_size - crop_size) / 2 + pad_size
    upper_cut = (im_size + crop_size) / 2 + pad_size
    shift_x = frame_size / 2
    shift_y = shift_x
    tf_shift = AffineTransform(translation=[-shift_x, -shift_y])
    tf_shift_inv = AffineTransform(translation=[shift_x, shift_y])

    scaling_factor = 0.2 * np.random.random() + 0.9
    angle = 2 * pi * (np.random.random() - 0.5)
    trans_x = np.random.randint(-5, 5)
    trans_y = np.random.randint(-5, 5)

    tf = AffineTransform(scale=(scaling_factor, scaling_factor), rotation=angle, shear=None,
                         translation=(trans_x, trans_y))
    padded = warp(padded, (tf_shift + (tf + tf_shift_inv)).inverse)
    print "Padded shape after transform ", padded.shape

    # Crop to desired size
    tmp = padded[lower_cut:upper_cut, lower_cut:upper_cut, :]
    print "Finally, cuts and shape: ", lower_cut, upper_cut, padded.shape
    plt.imshow(tmp)


def get_errors(labels_file='data/train_labels.csv', predictions_file='models/training.csv'):
    labels = pd.read_csv(labels_file)
    predictions = pd.read_csv(predictions_file)
    error = pd.merge(labels, predictions, on=['id'])
    error['error'] = abs(error['genus_x'] - error['genus_y'])
    error = error.sort(columns='error')

from sklearn.metrics import roc_curve, auc

def plot_roc(y_true_file, y_pred_file, filename='ROC.png'):
    df = pd.merge(pd.read_csv(y_true_file), pd.read_csv(y_pred_file), on=['id'])
    y_true = df['genus_x'].values
    y_pred = df['genus_y'].values
    fpr, tpr, _ = roc_curve(y_true, y_pred)
    roc_auc = auc(fpr, tpr)
    plt.figure()
    plt.plot(fpr, tpr, label='ROC curve (area = %0.2f)' % roc_auc)
    plt.plot([0, 1], [0, 1], 'k--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver operating characteristic example')
    plt.legend(loc="lower right")
    plt.show()

import argparse


def GetOptions():
    """ Retrieve options from standard input """
    p = argparse.ArgumentParser(description='Neural net. training',
                                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument('network', metavar="network", type=str, default='VGG11',
                   help='Network name (should be defined in the model zoo).')
    p.add_argument('-b', '--batch-size', metavar="batch_size", type=int, default=56,
                   help='Batch size')
    p.add_argument('--max-epochs', metavar="max_epochs", type=int, default=50,
                   help='Minimum distance value')
    p.add_argument('--channels', metavar="channel", type=int, default=3,
                   help='Number of color channels (3 for RGB)')
    p.add_argument('--crop-size', metavar="crop_size", type=int, default=200,
                   help='Pictures batch data augmentation crop size.')
    p.add_argument('--train-file', metavar="train_file", type=str, default='train.npz',
                   help='Training set file.')
    p.add_argument('--test-file', metavar="test_file", type=str, default='test.npz',
                   help='Test set file.')
    p.add_argument('-d', '--data-aug', metavar="data_aug_type", type=str, default='full',
                   help='Batch data augmentation type')
    p.add_argument('-f', '--final-ratio', metavar="final_ratio", type=float, default=2.,
                   help='Batch over sampling final ratio (only relevant for resampling data-aug)')
    p.add_argument('--activation', metavar="activation", type=str, default='rectify',
                   help='Activation function (rectify, leaky_rectify, very_leaky_rectify) ')
    p.add_argument('--learning-init', metavar="learning_init", type=float, default=0.01,
                   help='Initial learning rate of Nesterov momentum method')
    p.add_argument('--learning-final', metavar="learning_final", type=float, default=0.0001,
                   help='Final learning rate of Nesterov momentum method')
    p.add_argument('--lambda2', metavar="lambda2", type=float, default=0.0005,
                   help='Lambda2 regularization term')
    p.add_argument('-l','--load', metavar="load", type=str, default=None,
                   help='Model to load (leave blank for none)')

    #p.add_argument('--boolean', action="store_true", dest="boolean", help='')
    args = vars(p.parse_args())
    return args
