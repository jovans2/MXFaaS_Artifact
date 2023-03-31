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
    t3 = time.time()
    download_stream = blob_client.download_blob()
    t4 = time.time()
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
    t3 = time.time()
    download_stream = blob_client.download_blob()
    t4 = time.time()
    my_blob.write(download_stream.readall())
model = joblib.load('lr_model.pk')
print('Model is ready')

fileAppend = open("../funcs.txt", "a")

def main(params):
    t1 = time.time()
    blobName = "in.txt"
    blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)
    with open(blobName, "wb") as my_blob:
        t3 = time.time()
        download_stream = blob_client.download_blob()
        t4 = time.time()
        my_blob.write(download_stream.readall())

    y = model.predict(X)

    value = y
    blobName = "out.txt"
    blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)
    t5 = time.time()
    blob_client.upload_blob(value, overwrite=True)
    t6 = time.time()
    t2 = time.time()
    print("--- LR-SERV ---", file=fileAppend)
    print("Handler time = ", t2-t1, file=fileAppend)
    print("Idle time = ", t4-t3+t6-t5, file=fileAppend)

main({"test":"func"})