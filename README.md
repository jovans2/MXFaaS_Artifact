# MXFaaS: Resource Sharing in Serverless Environments for Parallelism and Efficiency

MXFaaS is a novel serverless platform designed for high-efficiency. MXFaaS improves function performance by efficiently multiplexing processor
cycles, I/O bandwidth, and memory/processor state between
concurrently-executing instances of the same function. MXFaaS
introduces the new MXContainer abstraction, which can con-
currently execute multiple invocations of the same function and
owns a set of cores. To enable efficient use of processor cycles, the
MXContainer carefully helps schedule same-function invocations
for minimal response time. To enable efficient use of I/O band-
width, the MXContainer coalesces remote storage accesses and
remote function calls from same-function invocations. Finally, to
enable efficient use of memory/processor state, the MXContainer
first initializes function state and only later, on demand, spawns
a process per function invocation, so that all invocations share
unmodified memory state and minimize memory footprint 

This repository includes the prototype implementation of MXContainers, integration of MXFaaS with KNative, 
the scripts to perform the characterization study on the open-source
production-level traces and serverless benchmarks, and the
experiment workflow to run these workloads


## Artifact Description
Our artifact includes the prototype implementation of MXContainers, integration of MXFaaS with KNative,
the scripts to perform the characterization study on the open-source production-level traces and serverless benchmarks, and the experiment workflow to run these workloads. We have two main software portions. 

First, we provide scripts to reproduce our characterization study.
The scripts include the analyses of (i) the open-source production-level traces from Azure, and (ii) the open-source serverless benchmarks from FunctionBench.
The scripts analyze (i) the request burstiness in serverless environments, (ii) the idle time of serverless functions,
(iii) the breakdown of memory footprint of serverless functions,
and (iv) the bursty access pattern in to the remote storage.

Second, we provide our implementation of MXFaaS: a novel serverless platform built upon KNative. MXFaaS includes two main components: (i) MXContainers that support efficient CPU, I/O and memory sharing across invocations of the same function, 
and (ii) Node Controller that supports core assignment across collocated MXContainers and extends auto-scaling features.

## Hardware Dependencies

This artifact was tested on Intel (Haswell, Broadwell, Skylake), and AMD EPYC processors: Rome, Milan. Each processor has at least 8 cores.

## Software Dependencies

This artifact requires Ubuntu 18.04+, Docker 23.0.1, minikube v1.29.0, and KNative.

## Installation

First, clone our artifact repository:
<tt> git clone https://github.com/jovans2/MXFaaS_Artifact.git </tt>

### Setting up the environment
In the main directory of the repository, script <tt>setup.sh</tt>
installs all the software dependencies: <tt>./setup.sh</tt>.

The script will first install Docker and set up all the required privileges.
Then, it will install minikube, as a local Kubernetes, convenient for testing purposes.
Finally, it will install KNative.
The script will ask twice to choose one of multiple options. 
Both times choose the default value.

Once the installation is completed, open a new terminal and execute the following command <tt>minikube tunnel</tt>.

### Downloading open-source production-level traces
To reproduce our characterization study we need open source traces from the Azure's production workload.
We need (i) [<tt>Azure Functions Blob Access Trace</tt>](https://github.com/Azure/AzurePublicDataset/blob/master/AzureFunctionsBlobDataset2020.md), and 
(ii) [<tt>Azure Functions Invocation Trace</tt>](https://github.com/Azure/AzurePublicDataset/blob/master/AzureFunctionsInvocationTrace2021.md).
Download the traces in the <tt>characterization</tt> directory of our repository by running
<tt>./download-traces.sh</tt>.

### Installing application specific libraries
To locally install all the libraries needed by our Python applications, execute
<tt>./install-libs.sh</tt> in the characterization directory.
