import grpc
import sys
import time
import pool_controller_pb2
import pool_controller_pb2_grpc
from google.protobuf import empty_pb2

def run_client(port):
    # Create a gRPC channel and stub
    channel = grpc.insecure_channel(f'localhost:{port}')
    stub = pool_controller_pb2_grpc.PoolControllerStub(channel)

    # Add a new request
    print("Adding request with PID '1' and deadline 1000")
    add_request_response = stub.AddRequest(pool_controller_pb2.FunctionRequest(pid='1', deadline=1000))
    print("AddRequest response:", add_request_response)

    # Block the request
    print("Blocking request with PID '1'")
    block_request_response = stub.BlockRequest(pool_controller_pb2.RequestUpdate(pid='1', status=pool_controller_pb2.RequestStatus.RUNNING))
    print("BlockRequest response:", block_request_response)

    # Unblock the request
    print("Unblocking request with PID '1'")
    unblock_request_response = stub.UnblockRequest(pool_controller_pb2.RequestUpdate(pid='1', status=pool_controller_pb2.RequestStatus.BLOCKED))
    print("UnblockRequest response:", unblock_request_response)

    # Complete the request
    print("Completing request with PID '1'")
    complete_request_response = stub.CompleteRequest(pool_controller_pb2.RequestUpdate(pid='1', status=pool_controller_pb2.RequestStatus.RUNNING))
    print("CompleteRequest response:", complete_request_response)

    # Update core frequency
    print("Updating core frequency to 3000 MHz with 10 cores")
    update_core_freq_response = stub.UpdateCoreFrequency(pool_controller_pb2.CoreFrequencyUpdate(num_cores=10, frequency=3000))
    print("UpdateCoreFrequency response:", update_core_freq_response)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_client.py <port>")
        sys.exit(1)

    port = int(sys.argv[1])
    run_client(port)
