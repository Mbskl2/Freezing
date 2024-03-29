# -*- coding: utf-8 -*-
"""probyZwarstwami.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/18Mj2XYJ6GiDPYbiZ1jGp1QWsfYb7YSE2
"""

# Commented out IPython magic to ensure Python compatibility.
# %tensorflow_version 2.x
import tensorflow as tf
device_name = tf.test.gpu_device_name()
if device_name != '/device:GPU:0':
  raise SystemError('GPU device not found')
print('Found GPU at: {}'.format(device_name))

# Commented out IPython magic to ensure Python compatibility.
# %load_ext tensorboard

import datetime
!rm -rf ./logs/ # Clear any logs from previous runs
log_dir = "logs/fit/" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir=log_dir, histogram_freq=1)

"""TODO:


1. Dodać obsługę warstw konwolucyjnych. (/)
2. Nowe zestawy danych: https://www.tensorflow.org/datasets/catalog/kmnist , eurosat i higgs
3. Tesnsorboard
4. Zestaw + boosting + wariancja skuteczności/błędów dla jednego zestawu bosstingowego

"""

import numpy as np
import tensorflow as tf

class Freezing(tf.keras.layers.Wrapper):
  def __init__(self, frozen_percentage, layer):
    if not isinstance(layer, tf.keras.layers.Layer):
      raise ValueError(
          'Please initialize `Freezing` layer with a '
          '`tf.keras.layers.Layer` instance. You passed: {input}'.format(
              input=layer))
    self.frozen_percentage = frozen_percentage
    super().__init__(layer) 

  def call(self, input):
    return self.layer.call(input)

  def save_weights(self):
    self.__validate_layer(self.layer)
    layer_weights = self.layer.get_weights()[0]
    self.mask = self.__create_mask(layer_weights)
    self.old_weights = layer_weights[self.mask]

  def __validate_layer(self, layer):
    if len(layer.get_weights()) != 2: # weights and biases
      raise ValueError("Cannot freeze layers that don't have weights.")

  def __create_mask(self, layer_weights):
    # TODO: lepiej layer_weights.shape[0] czy *layer_weights[-1] ?
    frozen_neurons = np.random.rand(layer_weights.shape[0]) < self.frozen_percentage 
    mask = np.full(layer_weights.shape, False)
    mask[frozen_neurons, :] = True
    return mask

  def reset_weights(self):
    self.__set_weights_on_layer(self.layer, self.old_weights, self.mask)

  def __set_weights_on_layer(self, layer, old_weights, mask):
    weights = layer.get_weights()
    weights[0][mask] = old_weights
    layer.set_weights(weights)

class EnableFreezing(tf.keras.callbacks.Callback):
  def __init__(self, N = 1):
    if N < 1:
      raise ValueError(
          'The N parameter has to be a positive integer.'
          'You passed: {input}'.format(input=N))
    self.N = N

  def save_weights(self):
    for layer in self.model.layers:
      if isinstance(layer, Freezing):
        layer.save_weights()

  def reset_weights(self):
    for layer in self.model.layers:
      if isinstance(layer, Freezing):
        layer.reset_weights()

  def on_train_batch_end(self, batch, logs=None):
    self.reset_weights()

class EnableFreezingEveryNBatches(EnableFreezing):
  def __init__(self, N = 1):
    super().__init__(N)

  def on_train_batch_begin(self, batch, logs=None):
    if batch % self.N == 0:
      self.save_weights()

class EnableFreezingEveryNEpochs(EnableFreezing):
  def __init__(self, N = 1):
    super().__init__(N)

  def on_epoch_begin(self, epoch, logs=None):
    if epoch % self.N == 0:
      self.save_weights()

from tensorflow.keras.datasets import cifar10
from tensorflow.keras import utils
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Flatten, Conv2D, MaxPooling2D

num_classes = 10
num_epochs = 2

(x_train, y_train), (x_test, y_test) = cifar10.load_data()
x_train = x_train.astype('float32') / 255
x_test = x_test.astype('float32') / 255

y_train = tf.keras.utils.to_categorical(y_train, num_classes)
y_test = tf.keras.utils.to_categorical(y_test, num_classes)

# x_train.shape #(50000, 32, 32, 3)
# y_train.shape #(50000, 10)
# x_test.shape  #(10000, 32, 32, 3)
# y_test.shape  #(10000, 10)

model = Sequential()
model.add(Conv2D(32, (3, 3), activation='relu', input_shape=(32, 32, 3), kernel_initializer='he_uniform')) # With kern_init='glorot' conv layers sometimes don't learn
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Freezing(0.5, Conv2D(32, (3, 3), activation='relu', kernel_initializer='he_uniform')))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Flatten())
model.add(Freezing(0.5, Dense(150, activation='relu')))
model.add(Freezing(0.5, Dense(120, activation='relu')))
model.add(Freezing(0.5, Dense(num_classes, activation='softmax')))

model.compile(loss=tf.keras.losses.categorical_crossentropy,
                    optimizer=tf.keras.optimizers.Adam(),
                    metrics=['accuracy'])

model.fit(
    x_train,
    y_train, 
    batch_size=32,
    epochs=5, 
    callbacks=[EnableFreezingEveryNEpochs(), tensorboard_callback]) 
train_score = model.evaluate(x_train, y_train, verbose=0)
test_score = model.evaluate(x_test, y_test, verbose=0)

print(train_score, test_score)

for layer in model.layers: # - delete
  w = layer.get_weights() # - delete
  print(len(w)) # - delete
  for x in w: # - delete
    print(x.shape) # - delete
  print('**********') # - delete

layer_weights = np.random.rand(5, 2)
layer_weights

frozen_neurons = np.random.rand(layer_weights.shape[1]) < 0.5 
frozen_neurons

mask = np.full(layer_weights.shape, False)
mask

mask[:, frozen_neurons] = True
mask

# Commented out IPython magic to ensure Python compatibility.
# %tensorboard --logdir logs/fit