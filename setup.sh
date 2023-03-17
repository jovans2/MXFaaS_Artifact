sudo apt update
sudo apt upgrade -y
sudo apt-get install \
    ca-certificates \
    curl \
    gnupg \
    lsb-release htop -y
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin -y
sudo groupadd docker
sudo usermod -aG docker $USER

mkdir /tmp/114514
cd /tmp/114514

curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

sudo curl -fsSLo /usr/share/keyrings/kubernetes-archive-keyring.gpg https://packages.cloud.google.com/apt/doc/apt-key.gpg
echo "deb [signed-by=/usr/share/keyrings/kubernetes-archive-keyring.gpg] https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee /etc/apt/sources.list.d/kubernetes.list

sudo apt-get update
sudo apt-get install -y kubectl

wget https://github.com/knative/client/releases/download/knative-v1.8.1/kn-linux-amd64
chmod +x kn-linux-amd64
sudo mv kn-linux-amd64 /usr/local/bin/kn

wget https://github.com/knative-sandbox/kn-plugin-quickstart/releases/download/knative-v1.8.1/kn-quickstart-linux-amd64
chmod +x kn-quickstart-linux-amd64
sudo mv kn-quickstart-linux-amd64 /usr/local/bin/kn-quickstart

sudo chmod 666 /var/run/docker.sock

minikube start --nodes 1 -p minikube

# Install the required custom resources by running the command:
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.9.1/serving-crds.yaml

# Install the core components of Knative Serving by running the command:
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.9.1/serving-core.yaml

# Install the Knative Kourier controller by running the command: 
kubectl apply -f https://github.com/knative/net-kourier/releases/download/knative-v1.9.1/kourier.yaml

# Configure Knative Serving to use Kourier by default by running the command: 
kubectl patch configmap/config-network \
  --namespace knative-serving \
  --type merge \
  --patch '{"data":{"ingress-class":"kourier.ingress.networking.knative.dev"}}'

# Configure DNS
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.9.1/serving-default-domain.yaml


sudo apt-get install python3-pip
pip3 install numpy