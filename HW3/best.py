# -*- coding: utf-8 -*-
"""MLHW3.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1smUE-r-hqh30NqnZ12ZmBhhoPRqS9w0B
"""

# Code to read csv file into Colaboratory:
!pip install -U -q PyDrive
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from google.colab import auth
from oauth2client.client import GoogleCredentials
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# Authenticate and create the PyDrive client.  #用來驗證
auth.authenticate_user()
gauth = GoogleAuth()
gauth.credentials = GoogleCredentials.get_application_default()
drive = GoogleDrive(gauth)

#這邊的link是檔案共用連結
link1 = 'https://drive.google.com/open?id=1H7niqn4Eprrh9KK6ap7-iecgkHtjacQt' 
link2 = 'https://drive.google.com/open?id=1UViX4dyUtR-BCnZcgVot2yHlaeYe1Ffh'  
# Verify that you have everything after '='
fluff, id1 = link1.split('=') 
fluff, id2 = link2.split('=') 


#這邊要放檔案名稱
downloaded1 = drive.CreateFile({'id':id1}) 
downloaded2 = drive.CreateFile({'id':id2}) 
downloaded1.GetContentFile('train.csv') 
downloaded2.GetContentFile('test.csv') 
df = pd.read_csv('train.csv')
df_testing = pd.read_csv('test.csv')

#把data做validation
from sklearn.model_selection import train_test_split
X = df.drop('label', axis = 1)
Y = df['label']
X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size = 0.3, random_state = 3)

#轉成可以用的data模式
def shape_CNN(data):
  temp = []
  for i in range(data.shape[0]):
    temp.append(np.array(data.iloc[i,0].split(" "), dtype = 'float').reshape(48, 48, 1))  #第一個1代表色階
  return np.array(temp) / 255  #做個標準化

from keras.utils import np_utils

X_train = shape_CNN(X_train)
X_test = shape_CNN(X_test)
Y_train = np_utils.to_categorical(Y_train, 7)
Y_test = np_utils.to_categorical(Y_test, 7)

import keras
from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation, Flatten, BatchNormalization, AveragePooling2D
from keras.layers import Conv2D, MaxPooling2D
from keras.layers import LeakyReLU
from keras.layers.advanced_activations import PReLU
from keras.utils import np_utils
from keras.preprocessing.image import ImageDataGenerator

"""使用較多參數的CNN去Build"""

def identity_block(model, num_filter, kernel_size, pool_size, dropout_rate, dropout_seed, CNN = True,input_detect = False):
  
  kernel_initializer = keras.initializers.glorot_normal()
  if CNN == True:
    if input_detect == True:
      model.add(Conv2D(filters = num_filter, kernel_size = kernel_size, input_shape = (48,48,1), padding = 'same', kernel_initializer = kernel_initializer))
      model.add(LeakyReLU())
      model.add(BatchNormalization())
      model.add(MaxPooling2D(pool_size= pool_size, padding='same'))
      model.add(Dropout(rate = dropout_rate, seed = dropout_seed))
    else:
      model.add(Conv2D(filters = num_filter, kernel_size = kernel_size, padding = 'same', kernel_initializer = kernel_initializer))
      model.add(LeakyReLU())
      model.add(BatchNormalization())
      model.add(MaxPooling2D(pool_size= pool_size, padding='same'))
      model.add(Dropout(rate = dropout_rate, seed = dropout_seed))
    return model
  else:
    model.add(Dense(units = num_filter, kernel_initializer = kernel_initializer))
    model.add(LeakyReLU())
    model.add(BatchNormalization())
    model.add(Dropout(rate = dropout_rate, seed = dropout_seed))
    return model

epochs = 20
batch_size = 64
drouput_seed = 10
dropout_rate = 0.25
pic_size = 48
kernel_size = (3,3)
pool_size = (2,2)


model = Sequential()
model = identity_block(model, 512, kernel_size = kernel_size, pool_size = pool_size, dropout_rate = dropout_rate, dropout_seed = dropout_rate, input_detect = True)
model = identity_block(model, 512, kernel_size = kernel_size, pool_size = pool_size, dropout_rate = dropout_rate, dropout_seed = dropout_rate)
model = identity_block(model, 768, kernel_size = kernel_size, pool_size = pool_size, dropout_rate = dropout_rate, dropout_seed = dropout_rate)
model = identity_block(model, 768, kernel_size = kernel_size, pool_size = pool_size, dropout_rate = dropout_rate, dropout_seed = dropout_rate)

model.add(Flatten())

model = identity_block(model, 512, kernel_size = kernel_size, pool_size = pool_size, dropout_rate = dropout_rate, dropout_seed = dropout_rate, CNN = False)
model = identity_block(model, 512, kernel_size = kernel_size, pool_size = pool_size, dropout_rate = dropout_rate, dropout_seed = dropout_rate, CNN = False)

model.add(Dense(units=7, activation='softmax', kernel_initializer='glorot_normal'))
model.compile(loss='categorical_crossentropy', optimizer="adamax", metrics=['accuracy'])
model.summary()

img_gen = ImageDataGenerator(rotation_range=30, width_shift_range=0.2, height_shift_range=0.2, zoom_range=[0.8, 1.2], shear_range=0.2, horizontal_flip=True)
History = model.fit_generator(img_gen.flow(X_train, Y_train, batch_size = 32), validation_data=(X_test, Y_test),
                              steps_per_epoch=len(X_train)/16, epochs=30)

"""使用Resnet34去建構模型"""

# data argumentation

import numpy as np
import keras
from keras.datasets import mnist
from keras.utils import np_utils
from keras.models import Sequential
from keras.layers import Dense, Activation, Conv2D, MaxPooling2D, Flatten,Dropout,BatchNormalization,AveragePooling2D,concatenate,Input, Add
from keras.models import Model,load_model
from keras.optimizers import Adam


from keras.preprocessing.image import ImageDataGenerator
img_gen = ImageDataGenerator(rotation_range=30, width_shift_range=0.2, height_shift_range=0.2, zoom_range=[0.8, 1.2], shear_range=0.2, horizontal_flip=True)

def Conv2d_BN(x, nb_filter,kernel_size, padding='same',strides=(1,1),name=None):
    if name is not None: ##幫Layer 命名罷了, 之後可以從中調出Layer的名稱
        bn_name = name + '_bn'
        conv_name = name + '_conv'
    else:
        bn_name = None
        conv_name = None

    #在一般Keras的layer, 可以直接把上一個model放到最後面並且括弧, 就可以代表兩個layer疊在一起
    x = Conv2D(nb_filter,kernel_size,padding=padding,strides=strides,activation='relu',name=conv_name)(x)
    x = BatchNormalization(axis=3,name=bn_name)(x)
    return x

def Residual_Block(input_model,nb_filter,kernel_size,strides=(1,1), with_conv_shortcut =False):
    x = Conv2d_BN(input_model,nb_filter=nb_filter,kernel_size=kernel_size,strides=strides,padding='same')
    x = Conv2d_BN(x, nb_filter=nb_filter, kernel_size=kernel_size,padding='same')
    
    #need convolution on shortcut for add different channel
    if with_conv_shortcut:
        shortcut = Conv2d_BN(input_model,nb_filter=nb_filter,strides=strides,kernel_size=kernel_size)
        x = Add()([x,shortcut])
        return x
    else:
        x = Add()([x,input_model])
        return x

def ResNet34(width, height, depth, classes):
    
    Img = Input(shape=(width,height,depth))
    
    x = Conv2d_BN(Img,64,(7,7),strides=(2,2),padding='same')
    x = MaxPooling2D(pool_size=(3,3),strides=(2,2),padding='same')(x)  

    #Residual conv2_x ouput 56x56x64 
    x = Residual_Block(x,nb_filter=64,kernel_size=(3,3))
    x = Residual_Block(x,nb_filter=64,kernel_size=(3,3))
    x = Residual_Block(x,nb_filter=64,kernel_size=(3,3))
    
    #Residual conv3_x ouput 28x28x128 
    x = Residual_Block(x,nb_filter=128,kernel_size=(3,3),strides=(2,2),with_conv_shortcut=True)# need do convolution to add different channel
    x = Residual_Block(x,nb_filter=128,kernel_size=(3,3))
    x = Residual_Block(x,nb_filter=128,kernel_size=(3,3))
    x = Residual_Block(x,nb_filter=128,kernel_size=(3,3))
    
    #Residual conv4_x ouput 14x14x256
    x = Residual_Block(x,nb_filter=256,kernel_size=(3,3),strides=(2,2),with_conv_shortcut=True)# need do convolution to add different channel
    x = Residual_Block(x,nb_filter=256,kernel_size=(3,3))
    x = Residual_Block(x,nb_filter=256,kernel_size=(3,3))
    x = Residual_Block(x,nb_filter=256,kernel_size=(3,3))
    x = Residual_Block(x,nb_filter=256,kernel_size=(3,3))
    x = Residual_Block(x,nb_filter=256,kernel_size=(3,3))
    
    #Residual conv5_x ouput 7x7x512
    x = Residual_Block(x,nb_filter=512,kernel_size=(3,3),strides=(2,2),with_conv_shortcut=True)
    x = Residual_Block(x,nb_filter=512,kernel_size=(3,3))
    x = Residual_Block(x,nb_filter=512,kernel_size=(3,3))


    #Using AveragePooling replace flatten
    x = AveragePooling2D()(x)
    x = Flatten()(x)
    x = Dense(classes,activation='softmax')(x)
    
    model=Model(input=Img,output=x)
    return model

Y_train.shape

Resnet_model = ResNet34(48,48,1,7)
Resnet_model.summary()
Resnet_model.compile(optimizer = Adam,loss = 'categorical_crossentropy',metrics=['accuracy'])

#Start training using dataaugumentation generator
History = Resnet_model.fit_generator(img_gen.flow(X_train, Y_train, batch_size = 128),
                                     steps_per_epoch = len(X_train)/16, 
                                     validation_data = (X_test,Y_test), 
                                     epochs = 20 )

"""底下是一般的CNN Model"""

#常數
epochs = 30
batch_size = 64

nb_classes = 7
input_shape = (1, 48, 48)

filters_num = 256
dropout_rate = 0.2


#模型本身
model = Sequential()
model.add(Convolution2D(filters = filters_num, kernel_size = (3, 3), 
                        padding = 'same', 
                        input_shape = input_shape, 
                        data_format='channels_first'))

model.add(BatchNormalization())
model.add(LeakyReLU())
model.add(MaxPooling2D(pool_size = (2,2), padding = 'same'))
model.add(Dropout(dropout_rate))

model.add(Convolution2D(filters_num, kernel_size = (3,3), padding = 'same'))
model.add(BatchNormalization())
model.add(LeakyReLU())
model.add(MaxPooling2D(pool_size = (2,2), padding = 'same'))
model.add(Dropout(dropout_rate))

model.add(Convolution2D(filters_num, kernel_size = (3,3), padding = 'same'))
model.add(BatchNormalization())
model.add(LeakyReLU())
model.add(MaxPooling2D(pool_size = (2,2), padding = 'same'))
model.add(Dropout(dropout_rate))

model.add(Convolution2D(filters_num, kernel_size = (3,3), padding = 'same'))
model.add(BatchNormalization())
model.add(LeakyReLU())
model.add(MaxPooling2D(pool_size = (2,2), padding = 'same'))
model.add(Dropout(dropout_rate))


#Flatten
model.add(Flatten())
model.add(Dense(256)) #進入full connect
model.add(BatchNormalization())
model.add(LeakyReLU())
model.add(Dropout(rate = dropout_rate))

model.add(Dense(256))
model.add(BatchNormalization())
model.add(LeakyReLU())
model.add(Dropout(dropout_rate))
    
model.add(Dense(nb_classes))
model.add(Activation('softmax'))
model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

#實際上建模
Histroy = model.fit(X_train, Y_train, validation_data=(X_test, Y_test), batch_size = batch_size, epochs = epochs)

def show_train_history(train_history, train, validation):
    plt.plot(train_history.history[train])
    plt.plot(train_history.history[validation])
    plt.title('Train History')
    plt.ylabel('train')
    plt.xlabel('Epoch')
    plt.legend(['train', 'validation'], loc='center right')
    plt.show()

show_train_history(train_histroy, 'acc', 'val_acc')

"""以下用VGG net的方式去做"""

def VGGNet(width, height, depth, classes):
    
    model = Sequential()
    
    model.add(Conv2D(64,(3,3),strides=(1,1),input_shape=(width, height, depth),padding='same',activation='relu'))
    model.add(BatchNormalization())
    model.add(Conv2D(64,(3,3),strides=(1,1),padding='same',activation='relu'))
    model.add(BatchNormalization())
    model.add(MaxPooling2D(pool_size=(2,2)))
    
    
    model.add(Conv2D(128,(3,2),strides=(1,1),padding='same',activation='relu'))
    model.add(BatchNormalization())
    model.add(Conv2D(128,(3,3),strides=(1,1),padding='same',activation='relu'))
    model.add(BatchNormalization())
    model.add(MaxPooling2D(pool_size=(2,2)))
    model.add(Conv2D(256,(3,3),strides=(1,1),padding='same',activation='relu'))
    model.add(BatchNormalization())
    model.add(Conv2D(256,(3,3),strides=(1,1),padding='same',activation='relu'))
    model.add(BatchNormalization())
    model.add(Conv2D(256,(3,3),strides=(1,1),padding='same',activation='relu'))
    model.add(BatchNormalization())
    model.add(MaxPooling2D(pool_size=(2,2)))
    
    model.add(Conv2D(512,(3,3),strides=(1,1),padding='same',activation='relu'))
    model.add(BatchNormalization())
    model.add(Conv2D(512,(3,3),strides=(1,1),padding='same',activation='relu'))
    model.add(BatchNormalization())
    model.add(Conv2D(512,(3,3),strides=(1,1),padding='same',activation='relu'))
    model.add(BatchNormalization())
    model.add(MaxPooling2D(pool_size=(2,2)))
    model.add(Conv2D(512,(3,3),strides=(1,1),padding='same',activation='relu'))
    model.add(BatchNormalization())
    model.add(Conv2D(512,(3,3),strides=(1,1),padding='same',activation='relu'))
    model.add(BatchNormalization())
    model.add(Conv2D(512,(3,3),strides=(1,1),padding='same',activation='relu'))
    model.add(BatchNormalization())
    model.add(MaxPooling2D(pool_size=(2,2)))
    
    model.add(Flatten())
    model.add(Dense(4096,activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(4096,activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(1000,activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(classes, activation='softmax'))
    
    model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
    
    return model

# 這個Net幾乎Train不起來@@

batch_size = 64
epochs = 20

VGG_model = VGGNet(48,48,1,7)

img_gen = ImageDataGenerator(rotation_range=30, width_shift_range=0.2, height_shift_range=0.2, zoom_range=[0.8, 1.2], shear_range=0.2, horizontal_flip=True)

Histroy = VGG_model.fit_generator(img_gen.flow(X_train, Y_train, batch_size = 16),
                                  steps_per_epoch = len(X_train)/16, validation_data=(X_test, Y_test), epochs = epochs)

"""其他種形式（4層, 128 -> 256 -> 512 -> 768）"""

epochs = 20
batch_size = 64
drouput_seed = 10
dropout_rate = 0.25
pic_size = 48
kernel_size = (3,3)
pool_size = (2,2)


model = Sequential()
model = identity_block(model, 128, kernel_size = kernel_size, pool_size = pool_size, dropout_rate = dropout_rate, dropout_seed = dropout_rate, input_detect = True)
model = identity_block(model, 256, kernel_size = kernel_size, pool_size = pool_size, dropout_rate = dropout_rate, dropout_seed = dropout_rate)
model = identity_block(model, 512, kernel_size = kernel_size, pool_size = pool_size, dropout_rate = dropout_rate, dropout_seed = dropout_rate)
model = identity_block(model, 768, kernel_size = kernel_size, pool_size = pool_size, dropout_rate = dropout_rate, dropout_seed = dropout_rate)

model.add(Flatten())

model = identity_block(model, 512, kernel_size = kernel_size, pool_size = pool_size, dropout_rate = dropout_rate, dropout_seed = dropout_rate, CNN = False)
model = identity_block(model, 512, kernel_size = kernel_size, pool_size = pool_size, dropout_rate = dropout_rate, dropout_seed = dropout_rate, CNN = False)

model.add(Dense(units=7, activation='softmax', kernel_initializer='glorot_normal'))
model.compile(loss='categorical_crossentropy', optimizer="adamax", metrics=['accuracy'])
model.summary()

img_gen = ImageDataGenerator(rotation_range=30, width_shift_range=0.2, height_shift_range=0.2, zoom_range=[0.8, 1.2], shear_range=0.2, horizontal_flip=True)
History = model.fit_generator(img_gen.flow(X_train, Y_train, batch_size = 32), validation_data=(X_test, Y_test),
                              steps_per_epoch=len(X_train)/16, epochs=30)

"""最後的預測部分"""

df_testing = df_testing.drop('id', axis = 1)
df_testing = shape_CNN(df_testing)
result_final = model.predict(df_testing)

#result_final = Resnet_model.predict(df_testing)

#這邊的link是檔案共用連結
link = 'https://drive.google.com/open?id=1yepojaAl2GifRYXoqkLZq_5LAJNkhVpn'  
# Verify that you have everything after '='
fluff, id = link.split('=') 


#這邊要放檔案名稱
downloaded = drive.CreateFile({'id':id}) 
downloaded.GetContentFile('sample.csv') 
sample_submission = pd.read_csv('sample.csv', header = 0,encoding = 'unicode_escape')

for i in range(result_final.shape[0]):
  sample_submission.iloc[i,1] = int(np.argmax(result_final[i]))

from google.colab import files
sample_submission.to_csv('submit.csv', index = False)
files.download('submit.csv')