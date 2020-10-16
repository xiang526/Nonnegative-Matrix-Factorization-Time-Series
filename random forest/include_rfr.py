#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time

from sklearn.ensemble import RandomForestRegressor
from sklearn.datasets import make_regression
from sklearn.metrics import mean_absolute_error
from sklearn.preprocessing import MinMaxScaler, MaxAbsScaler

import os
os.environ['TF_CPP_MIN_LOG_LEVEL']='2'

import tensorflow as tf
from keras.layers import SimpleRNN, LSTM, GRU, Bidirectional, Conv1D, MaxPooling1D, Dropout
from keras.models import Sequential
from keras.layers import Dense

# %%

def norm(vector):
    vector = np.array(vector)
    if (np.count_nonzero(vector) == 0):
        return 0.0
    else:
        return np.sqrt(np.sum(np.power(vector,2)))

def norml1(vector):
    vector = np.array(vector)
    if (np.count_nonzero(vector) == 0):
        return 0.0
    else:
        return np.sum(np.abs(vector))
    
def rrmse(y_true, y_pred):
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    if (np.count_nonzero(y_true - y_pred) == 0):
        return 0.0
    else:
        return norm(y_true - y_pred) / norm(y_true)

def mpe(y_true, y_pred):
    if (y_true == y_pred).all():
        return 0.0
    else:
        return np.linalg.norm(y_true - y_pred, 1) / np.linalg.norm(y_true, 1)

def l1_error(y_true, y_pred):
    if (y_true == y_pred).all():
        return 0.0
    else:
        return np.linalg.norm(y_true - y_pred, 1) / np.size(y_true)

def l2_error(y_true, y_pred):
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    if (np.count_nonzero(y_true - y_pred) == 0):
        return 0.0
    else:
        return norm(y_true - y_pred) / np.size(y_true)

# %%

def split_sequence(sequence, n_steps_in, n_steps_out):
    X, y = list(), list()
    for i in range(len(sequence)):
        end_ix = i + n_steps_in
        out_end_ix = end_ix + n_steps_out
        if out_end_ix > len(sequence):
            break
        seq_x, seq_y = sequence[i:end_ix], sequence[end_ix:out_end_ix]
        X.append(seq_x)
        y.append(seq_y)
    return np.array(X), np.array(y)


def ext_archetype(d, d0, X_trainA, activation='relu', model_dl=GRU, rfr=True, time_window=28, max_depth=2, cnn=True, unit=20):
    
    es = tf.keras.callbacks.EarlyStopping(monitor='loss',  patience=5, verbose=0, mode='auto',)
    
    if rfr:
        # scaler = MinMaxScaler(feature_range=(0, 1)) 
        # X_trainA = scaler.fit_transform(X_trainA.reshape(-1, 1)).flatten()
        X_t, y_t = split_sequence(X_trainA, time_window, d-d0)
        regr_rf = RandomForestRegressor(max_depth=2, criterion='mse')
        regr_rf.fit(X_t, y_t)
        H_test1 = X_trainA[np.shape(X_trainA)[0]-time_window:np.shape(X_trainA)[0]]
        H_test1 = H_test1.reshape((1, time_window))
        test_predict= regr_rf.predict(H_test1)        
        # test_predict = scaler.inverse_transform(test_predict.reshape(-1, 1)).flatten()
    else:
        es = tf.keras.callbacks.EarlyStopping(monitor='loss',  patience=5, verbose=0, mode='auto',)
        scaler = MinMaxScaler(feature_range=(0, 1)) 
        X_train1 = scaler.fit_transform(X_trainA.reshape(-1, 1)).flatten()
        X_t, y_t = split_sequence(X_train1, time_window, d-d0)
        
        model = Sequential()
        X_t = X_t.reshape((X_t.shape[0], X_t.shape[1], 1))
        
        if cnn:  
            model.add(Conv1D(128, 1, activation=activation, input_shape=(time_window, 1)))
            model.add(MaxPooling1D(pool_size=4))
            model.add(Dropout(0.2))
            
        model.add(model_dl(unit, input_shape=(time_window, 1)))    
        model.add(Dense(d-d0))
        model.compile(loss='mean_absolute_error', optimizer='adam')
        model.fit(X_t, y_t, epochs=5000, batch_size=100, callbacks=[es], verbose=0)
        H_test1 = X_train1[np.shape(X_trainA)[0]-time_window:np.shape(X_train1)[0]]
        H_test1 = H_test1.reshape((1, time_window, 1))
        test_predict = model.predict(H_test1)    
        test_predict = scaler.inverse_transform(test_predict.reshape(-1, 1)).flatten()
    return test_predict

# %%

def trajectory_plot(trajectory, original, reconstructed):
    f = plt.subplots()
    plt.plot(original[trajectory, :], label="Original")
    plt.plot(reconstructed[trajectory, :], label="Reconstructed")
    plt.legend()
    plt.savefig("trajectories/trajectory_X_%s.pdf" % (trajectory))
    plt.show()

# %%



