import os
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

def lambda_handler():

    t1 = time.time()
    blobName = df_name
    dnld_blob.download_blob_new(blobName)
    full_blob_name = df_name.split(".")
    proc_blob_name = full_blob_name[0] + "_" + str(os.getpid()) + "." + full_blob_name[1]
    t2 = time.time()
    print("Time 1 = " + str(t2-t1))

    df = pd.read_csv(proc_blob_name)
    df['train'] = df['Text'].apply(cleanup)

    model = LogisticRegression(max_iter=10)
    tfidf_vector = TfidfVectorizer(min_df=1000).fit(df['train'])
    train = tfidf_vector.transform(df['train'])
    model.fit(train, df['Score'])
    t3 = time.time()
    print("Time 2 = " + str(t3-t2))

    filename = 'finalized_model_'+str(os.getpid())+'.sav'
    pickle.dump(model, open(filename, 'wb'))

    fReadName = 'finalized_model_'+str(os.getpid())+'.sav'
    blobName = 'finalized_model_'+str(os.getpid())+'.sav'
    dnld_blob.upload_blob_new(blobName, fReadName)
    t4 = time.time()
    print("Time 3 = " + str(t4-t3))

    return {"Ok":"done"}