import grpc
from concurrent import futures
import time
import threading

import node_controller_pb2
import node_controller_pb2_grpc

# -------------------------------
# Configuration Constants
# -------------------------------

TOTAL_CORES = 16          # Total number of cores available on the server
REFRESH_INTERVAL = 10   # Refresh interval in seconds
WEIGHT_EXPONENT = 1      # Exponent P for weighting pools

# Frequency Levels (Example)
# 1: Low Frequency
# 2: Medium Frequency
# 3: High Frequency
FREQUENCY_LEVELS = [1, 2, 3]
MIN_FREQUENCY_LEVEL = 1
MAX_FREQUENCY_LEVEL = 3

# -------------------------------
# Helper Classes and Functions
# -------------------------------

class PoolData:
    """
    Class to store utilization data and assignment for a pool.
    """
    def __init__(self):
        self.utilization = None
        self.assignment = node_controller_pb2.Assignment(
            num_cores=0,
            frequency_level=2  # Default to medium frequency
        )

class NodeControllerServicer(node_controller_pb2_grpc.NodeControllerServicer):
    def __init__(self, profiling_data):
        self.profiling_data = profiling_data
        self.pools = {}  # Maps pool_id to PoolData
        self.lock = threading.Lock()
        self.refresh_thread = threading.Thread(target=self.refresh_assignments)
        self.refresh_thread.daemon = True
        self.refresh_thread.start()

    def UpdatePoolUtilization(self, request, context):
        pool_id = request.utilization.pool_id
        num_served_invocations = request.utilization.num_served_invocations
        avg_waiting_time = request.utilization.avg_waiting_time
        num_invocations_lower_freq_possible = request.utilization.num_invocations_lower_freq_possible
        num_invocations_increased_freq = request.utilization.num_invocations_increased_freq

        with self.lock:
            if pool_id not in self.pools:
                self.pools[pool_id] = PoolData()

            # Update utilization data
            self.pools[pool_id].utilization = {
                'num_served_invocations': num_served_invocations,
                'avg_waiting_time': avg_waiting_time,
                'num_invocations_lower_freq_possible': num_invocations_lower_freq_possible,
                'num_invocations_increased_freq': num_invocations_increased_freq
            }

            # Retrieve current assignment
            assignment = self.pools[pool_id].assignment

        return node_controller_pb2.UpdatePoolUtilizationResponse(
            assignment=assignment,
            message="Assignment retrieved successfully."
        )

    def refresh_assignments(self):
        """
        Periodically computes core assignments and frequency levels for all pools.
        """
        while True:
            time.sleep(REFRESH_INTERVAL)
            with self.lock:
                # Filter out pools without utilization data
                active_pools = {pid: pdata for pid, pdata in self.pools.items() if pdata.utilization is not None}

                if not active_pools:
                    print("No active pools to assign.")
                    continue

                # Step 1: Compute Weights
                weights = {}
                for pid, pdata in active_pools.items():
                    util = pdata.utilization
                    # Example weight calculation: (num_served_invocations) * (1 + avg_waiting_time)
                    weights[pid] = (util['num_served_invocations']) * (1 + util['avg_waiting_time'])

                # Step 2: Compute Weighted Sum
                weighted_sum = sum(w ** WEIGHT_EXPONENT for w in weights.values())

                if weighted_sum == 0:
                    print("Weighted sum is zero. Cannot assign cores.")
                    continue

                # Step 3: Assign Cores
                core_assignments = {}
                for pid, w in weights.items():
                    ni = int((w ** WEIGHT_EXPONENT) * TOTAL_CORES / weighted_sum)
                    core_assignments[pid] = ni

                # Handle remaining cores due to integer division
                assigned_cores = sum(core_assignments.values())
                remaining_cores = TOTAL_CORES - assigned_cores
                if remaining_cores > 0:
                    # Assign remaining cores to pools with the highest weights
                    sorted_pools = sorted(weights.items(), key=lambda x: x[1], reverse=True)
                    for pid, _ in sorted_pools:
                        if remaining_cores <= 0:
                            break
                        core_assignments[pid] += 1
                        remaining_cores -= 1

                # Step 4: Assign Frequency Levels
                for pid, ni in core_assignments.items():
                    util = active_pools[pid].utilization
                    freq_level = self.pools[pid].assignment.frequency_level  # Current frequency level

                    # Define thresholds or criteria for frequency adjustment

                    ratio_increased_freq = util['num_invocations_increased_freq'] / max(util['num_served_invocations'], 1)
                    ratio_lower_freq_possible = util['num_invocations_lower_freq_possible'] / max(util['num_served_invocations'], 1)

                    # Adjust frequency level based on ratios
                    if ratio_increased_freq > 0.5 and freq_level < MAX_FREQUENCY_LEVEL:
                        freq_level += 1
                    elif ratio_lower_freq_possible > 0.5 and freq_level > MIN_FREQUENCY_LEVEL:
                        freq_level -= 1
                    # Else, keep the current frequency level

                    # Update assignment
                    self.pools[pid].assignment.num_cores = ni
                    self.pools[pid].assignment.frequency_level = freq_level

                    print(f"Assigned to Pool {pid}: {ni} cores, Frequency Level {freq_level}")

    def shutdown(self):
        """
        Gracefully shuts down the server.
        """
        self.refresh_thread.join()

# -------------------------------
# Node Controller Server Setup
# -------------------------------

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    node_controller_pb2_grpc.add_NodeControllerServicer_to_server(
        NodeControllerServicer(profiling_data={}), server
    )
    server.add_insecure_port('[::]:50052')  # Node Controller listens on port 50052
    server.start()
    print("NodeController gRPC server is running on port 50052.")
    try:
        while True:
            time.sleep(86400)  # Keep the server running
    except KeyboardInterrupt:
        print("Shutting down the NodeController server.")
        server.stop(0)

if __name__ == "__main__":
    serve()
