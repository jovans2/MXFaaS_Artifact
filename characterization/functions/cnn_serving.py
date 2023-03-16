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

fileAppend = open("../funcs.txt", "a")

def lambda_handler():
    t1 = time.time()
    blobName = "img10.jpg"
    blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)
    with open(blobName, "wb") as my_blob:
        t3 = time.time()
        download_stream = blob_client.download_blob()
        t4 = time.time()
        my_blob.write(download_stream.readall())
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
    t2 = time.time()
    print("--- CNN SERVING ---", file=fileAppend)
    print("Handler time = ", t2-t1, file=fileAppend)
    print("Idle time = ", t4-t3, file=fileAppend)
    return inference

lambda_handler()