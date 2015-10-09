#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'thiebaut'
__date__ = '09/10/15'

import cPickle

from DataManager import DataManager

DM = DataManager()
DM.normalize()
DM.shuffle()
DM.save_to_lasagne_format(filename='train.pkl')

DM = DataManager(test=True)
DM.normalize()
DM.save_to_lasagne_format(filename='test.pkl')
