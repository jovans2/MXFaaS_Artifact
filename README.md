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
