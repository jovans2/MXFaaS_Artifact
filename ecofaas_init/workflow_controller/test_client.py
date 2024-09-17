import grpc
import workflow_controller_pb2
import workflow_controller_pb2_grpc

def run():
    # Connect to the server
    channel = grpc.insecure_channel('localhost:50051')
    stub = workflow_controller_pb2_grpc.WorkflowControllerStub(channel)

    # Prepare the request
    request = workflow_controller_pb2.OptimizeRequest(
        functions=['f1', 'f1'],  # Replace with desired function names
        slo=19.0  # Replace with desired SLO in milliseconds
    )

    # Send the request
    response = stub.OptimizeDeadlines(request)

    # Handle the response
    if response.message == "Optimization successful.":
        print("Optimal Per-Function Deadlines and Settings:")
        for deadline in response.deadlines:
            print(f"Function {deadline.function_name}:")
            print(f"  Frequency: {deadline.frequency} GHz")
            print(f"  Execution Time: {deadline.exec_time} ms")
            print(f"  Energy Consumption: {deadline.energy} J")
            print(f"  Deadline Fraction: {deadline.deadline_fraction:.2f}")
        print(f"Total Execution Time: {response.total_execution_time} ms")
        print(f"Total Energy Consumption: {response.total_energy} J")
    else:
        print(response.message)

if __name__ == "__main__":
    run()
