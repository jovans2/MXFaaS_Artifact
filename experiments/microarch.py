import os

affinity_mask = {0}
pid = os.getpid()
os.sched_setaffinity(pid, affinity_mask)

import time
from sklearn.feature_extraction.text import TfidfVectorizer
import joblib
import pandas as pd
import re
from azure.storage.blob import BlobServiceClient, BlobClient

connection_string = "DefaultEndpointsProtocol=https;AccountName=serverlesscache;AccountKey=O7MZkxwjyBWTcPL4fDoHi6n8GsYECQYiMe+KLOIPLpzs9BoMONPg2thf1wM1pxlVxuICJvqL4hWb+AStIKVWow==;EndpointSuffix=core.windows.net"
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client("artifacteval")

cleanup_re = re.compile('[^a-z]+')

def cleanup(sentence):
    sentence = sentence.lower()
    sentence = cleanup_re.sub(' ', sentence).strip()
    return sentence

blobName = "minioDataset.csv"
blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)
with open(blobName, "wb") as my_blob:
    download_stream = blob_client.download_blob()
    my_blob.write(download_stream.readall())
dataset = pd.read_csv('minioDataset.csv')

df_input = pd.DataFrame()
dataset['train'] = dataset['Text'].apply(cleanup)
tfidf_vect = TfidfVectorizer(min_df=100).fit(dataset['train'])
x = 'The ambiance is magical. The food and service was nice! The lobster and cheese was to die for and our steaks were cooked perfectly.  '
df_input['x'] = [x]
df_input['x'] = df_input['x'].apply(cleanup)
X = tfidf_vect.transform(df_input['x'])

x = 'My favorite cafe. I like going there on weekends, always taking a cafe and some of their pastry before visiting my parents.  '
df_input['x'] = [x]
df_input['x'] = df_input['x'].apply(cleanup)
X2 = tfidf_vect.transform(df_input['x'])

blobName = "lr_model.pk"
blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)
with open(blobName, "wb") as my_blob:
    download_stream = blob_client.download_blob()
    my_blob.write(download_stream.readall())
model = joblib.load('lr_model.pk')
print('Model is ready')

def lambda_handler_1():
    model.predict(X)

t1 = time.time()
child_pid = os.fork()
if child_pid == 0:
    lambda_handler_1()
    exit(-1)
else:
    output1 = os.popen("perf stat -e branches,branch-misses,L1-dcache-loads,L1-dcache-load-misses -p " + str(pid)).read()
    print(output1)
t2 = time.time()
rt1 = t2 - t1

lambda_handler_1()
lambda_handler_1()
lambda_handler_1()

t1 = time.time()
lambda_handler_1()
t2 = time.time()
rt2 = t2 - t1

print("LR Serve => Response time reduction = ", rt2/rt1)


import time
from mxnet import gluon
import mxnet as mx
from PIL import Image
from azure.storage.blob import BlobServiceClient, BlobClient

connection_string = "DefaultEndpointsProtocol=https;AccountName=serverlesscache;AccountKey=O7MZkxwjyBWTcPL4fDoHi6n8GsYECQYiMe+KLOIPLpzs9BoMONPg2thf1wM1pxlVxuICJvqL4hWb+AStIKVWow==;EndpointSuffix=core.windows.net"
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client("artifacteval")

net = gluon.model_zoo.vision.resnet50_v1(pretrained=True, root = '/tmp/')
net.hybridize(static_alloc=True, static_shape=True)
lblPath = gluon.utils.download('http://data.mxnet.io/models/imagenet/synset.txt',path='/tmp/')
with open(lblPath, 'r') as f:
    labels = [l.rstrip() for l in f]

def lambda_handler_2():
    blobName = "img10.jpg"
    image = Image.open(blobName)
    image.save('tempImage.jpeg')

    # format image as (batch, RGB, width, height)
    img = mx.image.imread("tempImage.jpeg")
    img = mx.image.imresize(img, 224, 224) # resize
    img = mx.image.color_normalize(img.astype(dtype='float32')/255,
                                mean=mx.nd.array([0.485, 0.456, 0.406]),
                                std=mx.nd.array([0.229, 0.224, 0.225])) # normalize
    img = img.transpose((2, 0, 1)) # channel first
    img = img.expand_dims(axis=0) # batchify

    prob = net(img).softmax() # predict and normalize output
    idx = prob.topk(k=5)[0] # get top 5 result
    inference = ''
    for i in idx:
        i = int(i.asscalar())
        # print('With prob = %.5f, it contains %s' % (prob[0,i].asscalar(), labels[i]))
        inference = inference + 'With prob = %.5f, it contains %s' % (prob[0,i].asscalar(), labels[i]) + '. '
    return inference

t1 = time.time()
lambda_handler_2()
t2 = time.time()
rt1 = t2 - t1

lambda_handler_2()
lambda_handler_2()
lambda_handler_2()

t1 = time.time()
lambda_handler_2()
t2 = time.time()
rt2 = t2 - t1

print("CNN Serve => Response time reduction = ", rt2/rt1)

import pickle
import torch
import rnn
import io
import string
import time
from azure.storage.blob import BlobServiceClient, BlobClient

connection_string = "DefaultEndpointsProtocol=https;AccountName=serverlesscache;AccountKey=O7MZkxwjyBWTcPL4fDoHi6n8GsYECQYiMe+KLOIPLpzs9BoMONPg2thf1wM1pxlVxuICJvqL4hWb+AStIKVWow==;EndpointSuffix=core.windows.net"
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client("artifacteval")

torch.set_num_threads(1)
language = 'Scottish'
language2 = 'Russian'
start_letters = 'ABCDEFGHIJKLMNOP'
start_letters2 = 'QRSTUVWXYZABCDEF'

blobName = "rnn_params.pkl"
blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)
with open(blobName, "wb") as my_blob:
    download_stream = blob_client.download_blob()
    my_blob.write(download_stream.readall())
my_blob = open(blobName, "rb")
params = pickle.load(my_blob)

all_categories =['French', 'Czech', 'Dutch', 'Polish', 'Scottish', 'Chinese', 'English', 'Italian', 'Portuguese', 'Japanese', 'German', 'Russian', 'Korean', 'Arabic', 'Greek', 'Vietnamese', 'Spanish', 'Irish']
n_categories = len(all_categories)
all_letters = string.ascii_letters + " .,;'-"
n_letters = len(all_letters) + 1

rnn_model = rnn.RNN(n_letters, 128, n_letters, all_categories, n_categories, all_letters, n_letters)
blobName = "rnn_model.pth"
blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)
with open(blobName, "wb") as my_blob:
    download_stream = blob_client.download_blob()
    my_blob.write(download_stream.readall())
my_blob = open(blobName, "rb")
buffer = io.BytesIO(my_blob.read())
rnn_model.load_state_dict(torch.load(buffer))
rnn_model.eval()

def lambda_handler_3():
    output_names = list(rnn_model.samples(language, start_letters))
    value = str(output_names)

    return {"Prediction":"correct"}

t1 = time.time()
lambda_handler_3()
t2 = time.time()
rt1 = t2 - t1

lambda_handler_3()
lambda_handler_3()
lambda_handler_3()

t1 = time.time()
lambda_handler_3()
t2 = time.time()
rt2 = t2 - t1

print("RNN Serve => Response time reduction = ", rt2/rt1)

import time
import pickle
from azure.storage.blob import BlobServiceClient, BlobClient
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import pandas as pd
import re
import warnings

warnings.filterwarnings("ignore")

cleanup_re = re.compile('[^a-z]+')

connection_string = "DefaultEndpointsProtocol=https;AccountName=serverlesscache;AccountKey=O7MZkxwjyBWTcPL4fDoHi6n8GsYECQYiMe+KLOIPLpzs9BoMONPg2thf1wM1pxlVxuICJvqL4hWb+AStIKVWow==;EndpointSuffix=core.windows.net"
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client("artifacteval")

def cleanup(sentence):
    sentence = sentence.lower()
    sentence = cleanup_re.sub(' ', sentence).strip()
    return sentence

df_name = 'minioDataset.csv'
df_path = 'pulled_' + df_name

blobName = df_name
blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)
with open(df_path, "wb") as my_blob:
    t3 = time.time()
    download_stream = blob_client.download_blob()
    t4 = time.time()
    my_blob.write(download_stream.readall())

def lambda_handler_4():
    df = pd.read_csv(df_path)
    df['train'] = df['Text'].apply(cleanup)

    model = LogisticRegression(max_iter=10)
    tfidf_vector = TfidfVectorizer(min_df=1000).fit(df['train'])
    train = tfidf_vector.transform(df['train'])
    model.fit(train, df['Score'])
    return {"Ok":"done"}

t1 = time.time()
lambda_handler_4()
t2 = time.time()
rt1 = t2 - t1

lambda_handler_4()
lambda_handler_4()
lambda_handler_4()

t1 = time.time()
lambda_handler_4()
t2 = time.time()
rt2 = t2 - t1

print("ML Train => Response time reduction = ", rt2/rt1)

import time
import cv2
from azure.storage.blob import BlobServiceClient, BlobClient

connection_string = "DefaultEndpointsProtocol=https;AccountName=serverlesscache;AccountKey=O7MZkxwjyBWTcPL4fDoHi6n8GsYECQYiMe+KLOIPLpzs9BoMONPg2thf1wM1pxlVxuICJvqL4hWb+AStIKVWow==;EndpointSuffix=core.windows.net"
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client("artifacteval")

tmp = "/tmp/"

vid_name = 'vid1.mp4'

result_file_path = tmp + vid_name
blobName = "vid1.mp4"
blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)
with open(vid_name, "wb") as my_blob:
    download_stream = blob_client.download_blob()
    my_blob.write(download_stream.readall())

def lambda_handler_5():
    
    video = cv2.VideoCapture(vid_name)

    width = int(video.get(3))
    height = int(video.get(4))
    fourcc = cv2.VideoWriter_fourcc(*'MPEG')
    out = cv2.VideoWriter('output.avi',fourcc, 20.0, (width, height))

    while video.isOpened():
        ret, frame = video.read()
        if ret:
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            tmp_file_path = tmp+'tmp.jpg'
            cv2.imwrite(tmp_file_path, gray_frame)
            gray_frame = cv2.imread(tmp_file_path)
            out.write(gray_frame)
            break
        else:
            break

    video.release()
    out.release()
    return

t1 = time.time()
lambda_handler_5()
t2 = time.time()
rt1 = t2 - t1

lambda_handler_5()
lambda_handler_5()
lambda_handler_5()

t1 = time.time()
lambda_handler_5()
t2 = time.time()
rt2 = t2 - t1

print("VidConv => Response time reduction = ", rt2/rt1)

import time
from PIL import Image
from azure.storage.blob import BlobServiceClient, BlobClient

connection_string = "DefaultEndpointsProtocol=https;AccountName=serverlesscache;AccountKey=O7MZkxwjyBWTcPL4fDoHi6n8GsYECQYiMe+KLOIPLpzs9BoMONPg2thf1wM1pxlVxuICJvqL4hWb+AStIKVWow==;EndpointSuffix=core.windows.net"
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client("artifacteval")

images = {}
for indI in range(0, 20):
    blbName = "img" + str(indI) + ".png"
    blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blbName)
    with open(blbName, "wb") as my_blob:
        download_stream = blob_client.download_blob()
        my_blob.write(download_stream.readall())
    images[blbName] = Image.open(blbName)

def lambda_handler_6():
    blobName = "img10.png"
    if blobName not in images:
        blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)
        with open(blobName, "wb") as my_blob:
            t3 = time.time()
            download_stream = blob_client.download_blob()
            t4 = time.time()
            my_blob.write(download_stream.readall())
        image = Image.open(blobName)
        images[blobName] = image
    else:
        image = images[blobName]
    width, height = image.size
    # Setting the points for cropped image
    left = 4
    top = height / 5
    right = 100
    bottom = 3 * height / 5
    im1 = image.crop((left, top, right, bottom))
    im1.save("newImage.png")

    return {"Image":"rotated"}

t1 = time.time()
lambda_handler_6()
t2 = time.time()
rt1 = t2 - t1

lambda_handler_6()
lambda_handler_6()
lambda_handler_6()

t1 = time.time()
lambda_handler_6()
t2 = time.time()
rt2 = t2 - t1

print("ImgRes => Response time reduction = ", rt2/rt1)

import time
from PIL import Image
from azure.storage.blob import BlobServiceClient, BlobClient

connection_string = "DefaultEndpointsProtocol=https;AccountName=serverlesscache;AccountKey=O7MZkxwjyBWTcPL4fDoHi6n8GsYECQYiMe+KLOIPLpzs9BoMONPg2thf1wM1pxlVxuICJvqL4hWb+AStIKVWow==;EndpointSuffix=core.windows.net"
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client("artifacteval")

blobName = "img10.jpg"
blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)
with open(blobName, "wb") as my_blob:
    t3 = time.time()
    download_stream = blob_client.download_blob()
    t4 = time.time()
    my_blob.write(download_stream.readall())

def lambda_handler_7():
    blobName = "img10.jpg"
    image = Image.open(blobName)
    img = image.transpose(Image.ROTATE_90)
    img.save('newImage.jpeg')
    fRead = open("newImage.jpeg","rb")
    value = fRead.read()
    blobName = "img10_rot.jpg"
    blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)
    blob_client.upload_blob(value, overwrite=True)
    return {"Image":"rotated"}

t1 = time.time()
lambda_handler_7()
t2 = time.time()
rt1 = t2 - t1

lambda_handler_7()
lambda_handler_7()
lambda_handler_7()

t1 = time.time()
lambda_handler_7()
t2 = time.time()
rt2 = t2 - t1

print("ImgRot => Response time reduction = ", rt2/rt1)

import time
import uuid
from azure.storage.blob import BlobServiceClient, BlobClient

connection_string = "DefaultEndpointsProtocol=https;AccountName=serverlesscache;AccountKey=O7MZkxwjyBWTcPL4fDoHi6n8GsYECQYiMe+KLOIPLpzs9BoMONPg2thf1wM1pxlVxuICJvqL4hWb+AStIKVWow==;EndpointSuffix=core.windows.net"
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client("artifacteval")

blobName = "ordIDs.txt"
ordID = 1
blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)
with open(blobName, "wb") as my_blob:
    download_stream = blob_client.download_blob()
    my_blob.write(download_stream.readall())

def lambda_handler_8():
    blobName = "ordIDs.txt"
    orderF = open(blobName, "r")
    orderIDs = orderF.readlines()
    orderPrice = -1
    for line in orderIDs:
        lineStr = line.split(" ")
        if int(lineStr[0]) == ordID:
            orderPrice = float(lineStr[1])
            break
    orderF.close()
    new_file = open("ordTemp.txt", "w")
    new_file.write(str(uuid.uuid1()) + " ---" + str(orderPrice))
    new_file.close()
    fRead = open("ordTemp.txt","rb")
    value = fRead.read()
    blobName = "ordPrice.txt"
    blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)
    blob_client.upload_blob(value, overwrite=True)
    return {"Order":"created"}

t1 = time.time()
lambda_handler_8()
t2 = time.time()
rt1 = t2 - t1

lambda_handler_8()
lambda_handler_8()
lambda_handler_8()

t1 = time.time()
lambda_handler_8()
t2 = time.time()
rt2 = t2 - t1

print("CreateOrd => Response time reduction = ", rt2/rt1)