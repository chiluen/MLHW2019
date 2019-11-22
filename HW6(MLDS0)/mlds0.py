# -*- coding: utf-8 -*-
"""MLDS0.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1UNkOAC7kBtx7aELinGjkLETtSev-W7oO
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
from keras.models import load_model

# Authenticate and create the PyDrive client.  #用來驗證
auth.authenticate_user()
gauth = GoogleAuth()
gauth.credentials = GoogleCredentials.get_application_default()
drive = GoogleDrive(gauth)

id1 = '1AynUnYPQkrFef9zo1JMeMJuYLtQoD5Bw'
id2 = '1ghvApulPA_6YIQMrDJ1pXQ7RiLULH7Qd'
id3 = '1fdgpyv-U9XbDcdcUkx6-vTOnaqAl9JLw'

#這邊要放檔案名稱
downloaded1 = drive.CreateFile({'id': id1})
downloaded2 = drive.CreateFile({'id': id2})
downloaded3 = drive.CreateFile({'id': id3})

downloaded1.GetContentFile('training_label.csv')
downloaded2.GetContentFile('testing_data.csv')
downloaded3.GetContentFile('sampleSubmission.csv')

#有些column問題, 以後直接改成csv讀檔
#df = pd.read_csv('training_label.csv', header = None)
#df_testing = pd.read_csv('testing_data.csv')

#先簡單處理training資料
import csv
word = []
label = []
with open('training_label.csv', newline='') as csvfile:
  rows = np.array(list(csv.reader(csvfile))[0:])
  for i in range(rows.shape[0]):
    temp = "".join(rows[i])
    temp = temp.split(' +++$+++ ') 
    label.append(float(temp[0]))
    word.append(temp[1])
  
word = np.array(word)
label = np.array(label)

import nltk
nltk.download('punkt') #可改斷詞

#做預處理, 把句子斷詞
word_tokenize = []
for i in range(word.shape[0]):
  word_tokenize.append( nltk.word_tokenize(word[i]) )

#word2vec, 每個詞轉換成100維度（or以上）
from gensim.models import Word2Vec
model = Word2Vec(word_tokenize, min_count=1, size = 100)
print('The number of vocabulary is', len(list(model.wv.vocab)))

from sklearn.model_selection import train_test_split
from keras.preprocessing.sequence import pad_sequences
from gensim.corpora.dictionary import Dictionary
from keras.utils import np_utils

def generate_id2wec(model, word2vec_size = 100):
  gensim_dict = Dictionary()
  gensim_dict.doc2bow(model.wv.vocab.keys(), allow_update=True)
  w2id = {v: k + 1 for k, v in gensim_dict.items()}  #把訓練好的詞語做編號, 並且弄成一個dict
  w2vec = {word: model[word] for word in w2id.keys()}  #利用前面的編碼, 把每一個id對應的vec(100維度的那個)對應出來
  n_vocabs = len(w2id) + 1
  embedding_weights = np.zeros((n_vocabs, word2vec_size))
  for w, index in w2id.items():  #從id1開始, 把這個embedding_weight矩陣全部填滿, 每一個row就是對應的vec
    embedding_weights[index, :] = w2vec[w]
  return w2id,embedding_weights
  
# text_to_array(w2id, word_tokenize[1:5])
def text_to_array(w2index, senlist):  # 將單詞表示成index(就是在哪一個id的意思)
  sentences_array = []
  for sen in senlist:
    new_sen = []
    for i in sen:
      try:
        new_sen.append(w2index.get(i,0))
      except:
        new_sen.append(0)
        
    #new_sen = [ w2index.get(i,0) for i in sen] 
    sentences_array.append(new_sen)
  return np.array(sentences_array)
  
def prepare_data(w2id, word_tokenize, label,max_len=150):
  X_train, X_test, Y_train, Y_test = train_test_split(word_tokenize,label, test_size=0.2)
  X_train = text_to_array(w2id, X_train)
  X_test = text_to_array(w2id, X_test)
  X_train = pad_sequences(X_train, maxlen=max_len) #這邊的重點, 要把每一個向量都弄成一樣長才行, 不然LSTM不能跑, 而這邊把向量弄成一樣長的技巧就是補零
  X_test = pad_sequences(X_test, maxlen=max_len)
  #return np.array(X_train), (Y_train) ,np.array(X_test), (Y_test)
  return np.array(X_train), np_utils.to_categorical(Y_train) ,np.array(X_test), np_utils.to_categorical(Y_test)

w2id,embedding_weights = generate_id2wec(model, 100)
X_train, Y_train, X_test , Y_test = prepare_data(w2id, word_tokenize,label, 150)

"""BidirectLSTM建置"""

import keras
from keras import Sequential
from keras.layers import Bidirectional,LSTM,Dense,Embedding,Dropout,Activation,Softmax, LeakyReLU, BatchNormalization
from keras.initializers import glorot_normal

class Sentiment:
  def __init__(self,w2id,embedding_weights,Embedding_dim,maxlen):
    self.Embedding_dim = Embedding_dim
    self.embedding_weights = embedding_weights
    self.vocab = w2id
    self.maxlen = maxlen
    self.model = self.build_model()
      
        
  def build_model(self):
    
    kernel_initializer = keras.initializers.Orthogonal()
    recurrent_initializer = keras.initializers.Orthogonal()
    Dropout_rate = 0.3
   
    model = Sequential()
    model.add(Embedding(output_dim = self.Embedding_dim,
                       input_dim=len(self.vocab)+1,
                       weights=[self.embedding_weights],
                       input_length=self.maxlen))
    model.add(Bidirectional(LSTM(64, activation='tanh', kernel_initializer=kernel_initializer, recurrent_initializer=recurrent_initializer, return_sequences=True),merge_mode='sum'))
    model.add(Bidirectional(LSTM(64, activation='tanh', kernel_initializer=kernel_initializer, recurrent_initializer=recurrent_initializer),merge_mode='sum'))
    
    model.add(Dense(32))
    model.add(LeakyReLU())
    model.add(BatchNormalization())
    model.add(Dropout(Dropout_rate))
    model.add(Dense(32))
    model.add(LeakyReLU())
    model.add(BatchNormalization())
    model.add(Dropout(Dropout_rate))
    
    model.add(Dense(2)) 
    model.add(Activation('softmax'))
    adam = keras.optimizers.Adam(lr=0.002, clipvalue=1, beta_1=0.9, beta_2=0.999, epsilon=None, decay=0.0)
    model.compile(loss='categorical_crossentropy', optimizer=adam, metrics=['accuracy'])
    model.summary()
    return model
  
  def train(self,X_train, y_train,X_test, y_test, epochs=5, batch_size = 64 ):
    self.model.fit(X_train, y_train, batch_size=32, epochs=epochs, validation_data=(X_test, y_test))  
  
  def predict(self, test_data):
    self.model.predict(test_data)

senti = Sentiment(w2id,embedding_weights,Embedding_dim = 100, maxlen = 150)

#要做的word: 把testing資料減少, 或許也可以把max len減少
X_train_shrinkage = X_train[0:50000,]
Y_train_shrinkage = Y_train[0:50000,]
X_test_shrinkage = X_test[0:2000,]
Y_test_shrinkage = Y_test[0:2000,]
senti.train(X_train_shrinkage,Y_train_shrinkage, X_test_shrinkage ,Y_test_shrinkage, epochs = 4, batch_size=32)
#temp_model.fit(X_train_shrinkage,Y_train_shrinkage, validation_data=(X_test ,Y_test), epochs = 4, batch_size=32)

"""特別處理部分"""

#先把之前Train的Data, 看ACC
#把那些ACC低的重Train一遍, 把這個模型特化成給這些ACC低的
#之前就有submission, 把那些ACC低的抓出來, 用新的模型再跑一次
#把最後跑出來的東西放到Submission裡面

ans_train = temp_model.predict(X_train)

train_not_well = []
for i in range(ans_train.shape[0]):
  if abs(ans_train[i][0] - ans_train[i][1]) < 0.05:
    train_not_well.append(i)
print(len(train_not_well))

#把這些Train_not_well的集合起來
X_train_notwell = X_train[train_not_well]
Y_train_notwell = Y_train[train_not_well]

Y_train_notwell.shape

temp_model.fit(X_train_notwell,Y_train_notwell, epochs = 3, batch_size=32)

id1 = '1TTz4ptBKc419Z8pr7ZAC5_2LSMiPY35n'
downloaded1 = drive.CreateFile({'id': id1})
downloaded1.GetContentFile('ans.npy')
ans = np.load('ans.npy')

#較差的id (in testing)
test_not_well = []
for i in range(ans.shape[0]):
  if abs(ans[i][0] - ans[i][1]) < 0.05:
    test_not_well.append(i)
print(len(test_not_well))

ans_fornotwell = temp_model.predict(test_data[test_not_well])

id1 = '1woaV1Gs2QhEpv3D-exewZDtTBrME4GxC'
downloaded1 = drive.CreateFile({'id': id1})
downloaded1.GetContentFile('submit.csv')
submission = pd.read_csv('submit.csv', header = 0,encoding = 'unicode_escape')

j = 0
for i in test_not_well:
  label = int(np.argmax(ans_fornotwell[j]))
  j+=1

  submission.iloc[i,1] = label

"""處理testing資料與最後的output"""

word_test = []
with open('testing_data.csv', newline='', ) as csvfile:
  rows = np.array(list(csv.reader(csvfile))[1:])
  for i in range(len(rows)):
    word_test.append("".join(rows[i][1:]))

word_test = np.array(word_test)

np.save("word_test.npy", word_test)

word_test_tokenize = []
for i in range(word_test.shape[0]):
  word_test_tokenize.append( nltk.word_tokenize(word_test[i]) )

# 把分詞過後的text轉成可被LSTM吃掉的東西
test_data = text_to_array(w2id, word_test_tokenize)
test_data = pad_sequences(test_data, maxlen= 150) #這邊的重點, 要把每一個向量都弄成一樣長才行, 不然LSTM不能跑, 而這邊把向量弄成一樣長的技巧就是補零
test_data = np.array(test_data)

#跑了半小時以上...
#ans = senti.model.predict(test_data)
ans = temp_model.predict(test_data)

np.save("ans.npy", ans)

submission = pd.read_csv('sampleSubmission.csv', header = 0,encoding = 'unicode_escape')
label = []
for i in range(ans.shape[0]):
  label.append(int(np.argmax(ans[i])))
  if i%10000 == 0:
    print("Data processing...", str(i/ans.shape[0]), "percent...")
submission = submission.drop(['label'], axis = 1)
submission['label'] = label

from google.colab import files
submission.to_csv('submit.csv', index = False)
files.download('submit.csv')