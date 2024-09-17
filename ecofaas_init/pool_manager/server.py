import grpc
from concurrent import futures
import time

import pool_manager_pb2
import pool_manager_pb2_grpc
import node_controller_pb2
import node_controller_pb2_grpc
from google.protobuf import empty_pb2

# Define REFRESH_INTERVAL and TOTAL_POOLS for simulation
REFRESH_INTERVAL = 60  # Match this with your actual refresh interval
TOTAL_POOLS = 3  # Number of pools for this simulation

class PoolManagerServicer(pool_manager_pb2_grpc.PoolManagerServicer):
    def __init__(self, node_controller_channel):
        self.node_controller_stub = node_controller_pb2_grpc.NodeControllerStub(node_controller_channel)
        self.pool_controllers = [
            'localhost:50054',  # Pool Controller 1
            'localhost:50055',  # Pool Controller 2
            'localhost:50056',  # Pool Controller 3
        ]

    def fetch_utilizations_from_pools(self):
        utilizations = []
        for pool_controller_address in self.pool_controllers:
            with grpc.insecure_channel(pool_controller_address) as channel:
                stub = pool_manager_pb2_grpc.PoolControllerStub(channel)
                response = stub.GetUtilizationStatus(empty_pb2.Empty())
                utilizations.extend(response.utilizations)
        return utilizations

    def update_pools_with_assignments(self, assignments):
        for i, pool_controller_address in enumerate(self.pool_controllers):
            with grpc.insecure_channel(pool_controller_address) as channel:
                stub = pool_manager_pb2_grpc.PoolControllerStub(channel)
                assignment = assignments[i]
                request = pool_manager_pb2.UpdateAssignmentRequest(
                    pool_id=assignment.pool_id,
                    start_core_id=assignment.start_core_id,
                    core_count=assignment.core_count,
                    frequency_level=assignment.frequency_level
                )
                stub.UpdateAssignment(request)

    def GetUtilizations(self, request, context):
        # Fetch utilizations from all Pool Controllers
        utilizations = self.fetch_utilizations_from_pools()

        # Send utilizations to Node Controller
        update_request = node_controller_pb2.UpdatePoolUtilizationsRequest(
            utilizations=utilizations
        )
        response = self.node_controller_stub.UpdatePoolUtilizations(update_request)

        # Send new assignments to Pool Controllers
        self.update_pools_with_assignments(response.assignments)

        return pool_manager_pb2.UpdateUtilizationsResponse(
            assignments=response.assignments,
            message="Utilizations processed and assignments updated."
        )

def serve():
    # Connect to the NodeController
    node_controller_channel = grpc.insecure_channel('localhost:50052')

    # Create a gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pool_manager_pb2_grpc.add_PoolManagerServicer_to_server(
        PoolManagerServicer(node_controller_channel), server
    )

    # Listen on port 50053
    server.add_insecure_port('[::]:50053')
    server.start()
    print("PoolManager gRPC server is running on port 50053.")
    try:
        while True:
            time.sleep(REFRESH_INTERVAL)
            # Periodic update logic can be placed here if needed
    except KeyboardInterrupt:
        print("Shutting down the server.")
        server.stop(0)

if __name__ == "__main__":
    serve()
