import time
import pickle
from azure.storage.blob import BlobServiceClient, BlobClient
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import pandas as pd
import re
import warnings
import dnld_blob

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
fileAppend = open("../funcs.txt", "a")

def lambda_handler():
    t1 = time.time()

    blobName = df_name
    blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)
    with open(df_path, "wb") as my_blob:
        t3 = time.time()
        download_stream = dnld_blob.download_blob_new(blob_client)
        t4 = time.time()
        my_blob.write(download_stream.readall())
    df = pd.read_csv(df_path)
    df['train'] = df['Text'].apply(cleanup)

    model = LogisticRegression(max_iter=10)
    tfidf_vector = TfidfVectorizer(min_df=1000).fit(df['train'])
    train = tfidf_vector.transform(df['train'])
    model.fit(train, df['Score'])

    filename = 'finalized_model.sav'
    pickle.dump(model, open(filename, 'wb'))

    fRead = open("finalized_model.sav","rb")
    value = fRead.read()
    blobName = "finalized_model.sav"
    blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)
    t5 = time.time()
    dnld_blob.upload_blob_new(blob_client, value)
    t6 = time.time()

    t2 = time.time()
    print("--- ML TRAIN ---", file=fileAppend)
    print("Handler time = ", t2-t1, file=fileAppend)
    print("Idle time = ", t4-t3+t6-t5, file=fileAppend)
    return {"Ok":"done"}