#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'thiebaut'
__date__ = '07/11/15'

import cPickle
import numpy as np
from datetime import date

from lasagne.nonlinearities import rectify, leaky_rectify, very_leaky_rectify

from utils import GetOptions, plot_loss, make_submission_file, load_numpy_arrays
from conv_net import build_network

args = GetOptions()

if args['activation'] == 'rectify':
    activation_function = rectify
elif args['activation'] == 'leaky_rectify':
    activation_function = leaky_rectify
elif args['activation'] == 'very_leaky_rectify':
    activation_function = very_leaky_rectify
else:
    raise ValueError('Unknown activation function')

print "Training parameters: ", args
X, y, images_id = load_numpy_arrays(args['train_file'])
sample_size = y.shape[0] - y.shape[0] % args['batch_size']
X = X[:sample_size]
y = y[:sample_size]

print "Train:"
print "X.shape:", X.shape
print "y.shape:", y.shape
y_counts = np.unique(y, return_counts=True)[1]
print "y value counts: ", y_counts

# Compute over-sampling of class 1
dataset_ratio =  float(y_counts[1])/y_counts[0]
print "Labels ratio: {:.2f}".format(dataset_ratio)

exp_name = args['network']

conv_net = build_network(network_name=exp_name, data_augmentation=args['data_aug'], lambda2=args['lambda2'],
                         max_epochs=args['max_epochs'], nb_channels=args['channels'], crop_size=args['crop_size'],
                         init_learning_rate=args['learning_init'], final_learning_rate=args['learning_final'],
 activation_function=activation_function,
                         batch_size=args['batch_size'], dataset_ratio=dataset_ratio, final_ratio=args['final_ratio'], 
verbose=True)

if args['load']:
    with open(args['load'], 'rb') as f:
        loaded_net = cPickle.load(f)
    conv_net.load_params_from(loaded_net)

conv_net.fit(X, y)

name = exp_name + '_'+ str(date.today())
with open('models/conv_net_'+name+'.pkl', 'wb') as f:
    cPickle.dump(conv_net, f, -1)
conv_net.save_params_to('models/params_'+name)

# ----- Train set ----
train_predictions = conv_net.predict_proba(X)
make_submission_file(train_predictions[:sample_size], images_id[:sample_size],
                     output_filepath='models/training_'+name+'.csv')
plot_loss(conv_net, "models/loss_"+name+".png", show=False)

# ----- Test set ----
X_test, _, images_id_test = load_numpy_arrays(args['test_file'])
print "Test:"
print "X_test.shape:", X_test.shape
predictions = conv_net.predict_proba(X_test)
make_submission_file(predictions, images_id_test, output_filepath='submissions/submission_'+name+'.csv')
