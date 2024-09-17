import grpc
import node_controller_pb2
import node_controller_pb2_grpc
import time

# Define REFRESH_INTERVAL to match the server configuration
REFRESH_INTERVAL = 10  # Match this with the server's REFRESH_INTERVAL

def run():
    # Connect to the NodeController server
    channel = grpc.insecure_channel('localhost:50052')
    stub = node_controller_pb2_grpc.NodeControllerStub(channel)

    # Example utilization data for multiple pools
    pool_utilizations = [
        node_controller_pb2.PoolUtilization(
            pool_id="pool_1",
            num_served_invocations=100,
            avg_waiting_time=50.0,  # in milliseconds
            num_invocations_lower_freq_possible=20,
            num_invocations_increased_freq=10
        ),
        node_controller_pb2.PoolUtilization(
            pool_id="pool_2",
            num_served_invocations=150,
            avg_waiting_time=30.0,
            num_invocations_lower_freq_possible=15,
            num_invocations_increased_freq=5
        ),
        node_controller_pb2.PoolUtilization(
            pool_id="pool_3",
            num_served_invocations=80,
            avg_waiting_time=70.0,
            num_invocations_lower_freq_possible=10,
            num_invocations_increased_freq=20
        ),
        # Add more pool data as needed
    ]

    # Send utilization data to the Node Controller
    for util in pool_utilizations:
        request = node_controller_pb2.UpdatePoolUtilizationRequest(
            utilization=util
        )
        response = stub.UpdatePoolUtilization(request)
        if response.assignment.num_cores > 0:
            print(f"Assignment for {util.pool_id}:")
            print(f"  Number of Cores: {response.assignment.num_cores}")
            print(f"  Frequency Level: {response.assignment.frequency_level}")
            print(f"  Message: {response.message}\n")
        else:
            print(f"Failed to get assignment for {util.pool_id}: {response.message}\n")

    # Keep the client running to allow periodic updates (optional)
    # Here, we simulate periodic updates every REFRESH_INTERVAL seconds
    try:
        while True:
            time.sleep(REFRESH_INTERVAL)
            # Update utilization data as needed
            # For example, send updated metrics
            # This part can be customized based on actual use-case
    except KeyboardInterrupt:
        print("Client shutting down.")

if __name__ == "__main__":
    run()
