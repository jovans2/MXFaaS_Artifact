import psutil
import os
pid = os.getpid()
python_process = psutil.Process(pid)
memoryUse_old = 0
import pickle
import torch
import rnn
import io
import string
from azure.storage.blob import BlobServiceClient, BlobClient

fileAppend = open("../funcs.txt", "a")

memoryUse = python_process.memory_info()[0]/2.**20  # memory use in MB
print("--- CNN SERVING ---", file=fileAppend)
print('memory use 1:', memoryUse-memoryUse_old, file=fileAppend)

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

memoryUse_old = memoryUse
memoryUse = python_process.memory_info()[0]/2.**20  # memory use in MB
print('memory use 2:', memoryUse-memoryUse_old, file=fileAppend)

def main(params):
    blobName = "in.txt"
    blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)
    with open(blobName, "wb") as my_blob:
        download_stream = blob_client.download_blob()
        my_blob.write(download_stream.readall())

    output_names = list(rnn_model.samples(language, start_letters))
    value = str(output_names)
    blobName = "out.txt"
    blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)
    blob_client.upload_blob(value, overwrite=True)

    return {"Prediction":"correct"}

main({"func":"test"})
memoryUse_old = memoryUse
memoryUse = python_process.memory_info()[0]/2.**20  # memory use in MB
print('memory use 3:', memoryUse-memoryUse_old, file=fileAppend)