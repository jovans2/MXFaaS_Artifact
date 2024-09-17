import grpc
from concurrent import futures
import subprocess
import time
import sys
import os
import signal
from google.protobuf import empty_pb2
import pool_controller_pb2
import pool_controller_pb2_grpc

TOTAL_CORES = 16  # Define as appropriate
CORE_FREQUENCY = 2000  # Define as appropriate (in MHz)
POOL_MANAGER_ADDRESS = 'localhost:50052'  # Address of the Pool Manager gRPC server
REFRESH_INTERVAL = 10  # Interval to send utilization data in seconds

class PoolControllerServicer(pool_controller_pb2_grpc.PoolControllerServicer):
    def __init__(self):
        self.requests = {}  # To keep track of requests by PID
        self.num_cores = TOTAL_CORES
        self.frequency = CORE_FREQUENCY
        self.start_core_id = 0  # Default start core ID
        self.core_count = TOTAL_CORES  # Default core count
        self.queue = []  # Queue for managing requests
        self.served_requests = 0
        self.total_waiting_time = 0.0
        self.avg_waiting_time = 0.0
        self.missed_requests = 0
        self.temp_freq_increases = 0

    def AddRequest(self, request, context):
        pid = request.pid
        deadline = request.deadline
        
        # Initialize request state
        self.requests[pid] = {
            'status': pool_controller_pb2.RequestStatus.WAITING, 
            'deadline': deadline,
            'arrival_time': time.time()  # Record the time when request is added
        }
        self.queue.append(pid)
        self.activate_requests()
        return empty_pb2.Empty()

    def BlockRequest(self, request, context):
        pid = request.pid
        if pid in self.requests and self.requests[pid]['status'] == pool_controller_pb2.RequestStatus.RUNNING:
            self.requests[pid]['status'] = pool_controller_pb2.RequestStatus.BLOCKED
            self.activate_requests()
        return empty_pb2.Empty()

    def UnblockRequest(self, request, context):
        pid = request.pid
        if pid in self.requests and self.requests[pid]['status'] == pool_controller_pb2.RequestStatus.BLOCKED:
            self.requests[pid]['status'] = pool_controller_pb2.RequestStatus.WAITING
            self.activate_requests()
        return empty_pb2.Empty()

    def CompleteRequest(self, request, context):
        pid = request.pid
        if pid in self.requests:
            # Calculate waiting time
            waiting_time = time.time() - self.requests[pid]['arrival_time']
            self.total_waiting_time += waiting_time

            del self.requests[pid]
            self.queue.remove(pid)
            self.served_requests += 1
            self.update_avg_waiting_time()
            self.activate_requests()
        return empty_pb2.Empty()

    def UpdateCoreFrequency(self, request, context):
        self.start_core_id = request.start_core_id
        self.core_count = request.core_count
        self.num_cores = self.core_count
        self.frequency = request.frequency

        self.served_requests = 0
        self.total_waiting_time = 0
        self.avg_waiting_time = 0
        self.missed_requests = 0
        self.temp_freq_increases = 0
        
        # Update the frequency for the specified cores
        for core_id in range(self.start_core_id, self.start_core_id + self.core_count):
            try:
                subprocess.run(["cpufreq-set", "-c", str(core_id), "-f", f"{self.frequency}MHz"], check=True)
                print(f"Core {core_id} frequency updated to {self.frequency} MHz")
            except Exception as e:
                print(f"Error updating frequency for core {core_id}: {e}")
        
        return empty_pb2.Empty()

    def SendUtilizationData(self, request, context):
        # Handle utilization data reception from Pool Manager
        self.served_requests = request.served_requests
        self.avg_waiting_time = request.avg_waiting_time
        self.missed_requests = request.missed_requests
        self.temp_freq_increases = request.temp_freq_increases
        return empty_pb2.Empty()

    def activate_requests(self):
        # Activate requests based on available cores and current queue
        running_pids = []
        for pid in list(self.queue):
            if len(running_pids) < self.num_cores:
                if self.requests[pid]['status'] == pool_controller_pb2.RequestStatus.WAITING:
                    self.requests[pid]['status'] = pool_controller_pb2.RequestStatus.RUNNING
                    running_pids.append(pid)

                    try:
                        os.kill(int(pid), signal.SIGCONT)
                        print(f"Sent SIGCONT to PID {pid}")
                    except ProcessLookupError:
                        print(f"Process with PID {pid} not found.")
                    except Exception as e:
                        print(f"Error sending SIGCONT to PID {pid}: {e}")
        
        print(f"Activated requests: {running_pids}")
        print(f"Current requests status: {self.requests}")

    def update_avg_waiting_time(self):
        if self.served_requests > 0:
            self.avg_waiting_time = self.total_waiting_time / self.served_requests
        else:
            self.avg_waiting_time = 0.0

    def send_utilization_data_periodically(self):
        # Send utilization data to the Pool Manager periodically
        with grpc.insecure_channel(POOL_MANAGER_ADDRESS) as channel:
            stub = pool_controller_pb2_grpc.PoolManagerStub(channel)
            while True:
                try:
                    utilization_data = pool_controller_pb2.UtilizationData(
                        served_requests=self.served_requests,
                        avg_waiting_time=self.avg_waiting_time,
                        missed_requests=self.missed_requests,
                        temp_freq_increases=self.temp_freq_increases
                    )
                    stub.SendUtilizationData(utilization_data)
                    print("Sent utilization data to Pool Manager")
                except Exception as e:
                    print(f"Error sending utilization data: {e}")
                time.sleep(REFRESH_INTERVAL)

def serve(port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pool_controller_pb2_grpc.add_PoolControllerServicer_to_server(PoolControllerServicer(), server)
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    print(f"PoolController gRPC server is running on port {port}.")
    try:
        while True:
            time.sleep(86400)  # One day in seconds
    except KeyboardInterrupt:
        print("Shutting down the server.")
        server.stop(0)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python pool_controller.py <port>")
        sys.exit(1)

    port = int(sys.argv[1])
    servicer = PoolControllerServicer()
    serve_thread = futures.ThreadPoolExecutor(max_workers=1).submit(serve, port)
    send_thread = futures.ThreadPoolExecutor(max_workers=1).submit(servicer.send_utilization_data_periodically)
