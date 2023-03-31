import psutil
import os
pid = os.getpid()
python_process = psutil.Process(pid)
memoryUse_old = 0
from sklearn.feature_extraction.text import TfidfVectorizer
import joblib
import pandas as pd
import re
from azure.storage.blob import BlobServiceClient, BlobClient

fileAppend = open("../funcs.txt", "a")

memoryUse = python_process.memory_info()[0]/2.**20  # memory use in MB
print("--- LR SERVING ---", file=fileAppend)
print('memory use 1:', memoryUse-memoryUse_old, file=fileAppend)

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

memoryUse_old = memoryUse
memoryUse = python_process.memory_info()[0]/2.**20  # memory use in MB
print('memory use 2:', memoryUse-memoryUse_old, file=fileAppend)

def main(params):
    blobName = "in.txt"
    blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)
    with open(blobName, "wb") as my_blob:
        download_stream = blob_client.download_blob()
        my_blob.write(download_stream.readall())

    y = model.predict(X)

    value = y
    blobName = "out.txt"
    blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)
    blob_client.upload_blob(value, overwrite=True)

main({"test":"func"})