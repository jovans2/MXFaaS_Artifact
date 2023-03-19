wget https://azurecloudpublicdataset2.blob.core.windows.net/azurepublicdatasetv2/azurefunctions_dataset2020/azurefunctions-accesses-2020.csv.bz2
bzip2 -d azurefunctions-accesses-2020.csv.bz2

sudo apt-get install unrar-free
wget https://github.com/Azure/AzurePublicDataset/raw/master/data/AzureFunctionsInvocationTraceForTwoWeeksJan2021.rar
unrar e AzureFunctionsInvocationTraceForTwoWeeksJan2021.rar
