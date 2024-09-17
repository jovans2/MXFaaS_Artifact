import pandas as pd
import pulp
import grpc
from concurrent import futures
import time

import workflow_controller_pb2
import workflow_controller_pb2_grpc

# -------------------------------
# Helper Functions
# -------------------------------

def load_profiling_data(csv_file):
    """
    Load profiling data from a CSV file and convert it into the required dictionary format.

    Parameters:
    - csv_file: str
        Path to the profiling CSV file.

    Returns:
    - profiling_data: dict
        Structure:
        {
            'function_name': [
                {'frequency': float, 'exec_time': float, 'energy': float},
                ...
            ],
            ...
        }
    """
    try:
        # Read the CSV file into a pandas DataFrame
        df = pd.read_csv(csv_file)

        # Validate required columns
        required_columns = {'function_name', 'frequency', 'exec_time', 'energy'}
        if not required_columns.issubset(df.columns):
            missing = required_columns - set(df.columns)
            raise ValueError(f"Missing columns in CSV: {missing}")

        # Initialize the profiling_data dictionary
        profiling_data = {}

        # Iterate over each row in the DataFrame
        for _, row in df.iterrows():
            func = row['function_name']
            freq = float(row['frequency'])
            exec_time = float(row['exec_time'])
            energy = float(row['energy'])

            # Initialize the list for the function if not already present
            if func not in profiling_data:
                profiling_data[func] = []

            # Append the frequency option as a dictionary
            profiling_data[func].append({
                'frequency': freq,
                'exec_time': exec_time,
                'energy': energy
            })

        return profiling_data

    except FileNotFoundError:
        print(f"Error: The file '{csv_file}' does not exist.")
        return {}
    except pd.errors.EmptyDataError:
        print("Error: The CSV file is empty.")
        return {}
    except pd.errors.ParserError:
        print("Error: The CSV file is malformed.")
        return {}
    except ValueError as ve:
        print(f"Error: {ve}")
        return {}

def optimize_deadlines(profiling_data, functions, slo):
    """
    Optimize per-function frequencies to minimize energy consumption while
    ensuring total execution time does not exceed the SLO.

    Parameters:
    - profiling_data: dict
        Structure:
        {
            'function_name': [
                {'frequency': float, 'exec_time': float, 'energy': float},
                ...
            ],
            ...
        }
    - functions: list of str
        List of function names to optimize.
    - slo: float
        Service Level Objective (maximum allowed total execution time)

    Returns:
    - dict
        {
            'per_function_deadlines': {
                'function_instance_name': {
                    'frequency': float,
                    'exec_time': float,
                    'energy': float,
                    'deadline_fraction': float
                },
                ...
            },
            'total_execution_time': float,
            'total_energy': float
        }
    """
    # Assign unique identifiers to each function instance
    unique_functions = []
    function_counts = {}
    for func in functions:
        if func in function_counts:
            function_counts[func] += 1
        else:
            function_counts[func] = 1
        unique_func = f"{func}_{function_counts[func]}"
        unique_functions.append(unique_func)

    # Filter profiling_data for the requested functions
    filtered_data = {}
    for unique_func in unique_functions:
        func_name = unique_func.rsplit('_', 1)[0]  # Extract the base function name
        options = profiling_data.get(func_name, [])
        if not options:
            raise ValueError(f"No profiling data available for function '{func_name}'.")
        filtered_data[unique_func] = options

    # Initialize the problem
    prob = pulp.LpProblem("Energy_Optimization", pulp.LpMinimize)

    # Decision variables
    decision_vars = {}
    for func, options in filtered_data.items():
        for idx, option in enumerate(options):
            var = pulp.LpVariable(f"{func}_opt{idx}", cat='Binary')
            decision_vars[(func, idx)] = var

    # Objective function: Minimize total energy
    prob += pulp.lpSum(
        option['energy'] * decision_vars[(func, idx)]
        for func, options in filtered_data.items()
        for idx, option in enumerate(options)
    ), "Total_Energy"

    # Constraints
    # 1. Each function instance must choose exactly one frequency
    for func, options in filtered_data.items():
        prob += pulp.lpSum(
            decision_vars[(func, idx)] for idx in range(len(options))
        ) == 1, f"One_frequency_for_{func}"

    # 2. Total execution time must not exceed SLO
    prob += pulp.lpSum(
        option['exec_time'] * decision_vars[(func, idx)]
        for func, options in filtered_data.items()
        for idx, option in enumerate(options)
    ) <= slo, "SLO_constraint"

    # Solve the problem
    solver = pulp.PULP_CBC_CMD(msg=0)  # msg=0 suppresses solver output
    prob.solve(solver)

    # Check if a solution was found
    if pulp.LpStatus[prob.status] != 'Optimal':
        raise Exception("No optimal solution found.")

    # Extract the chosen frequencies and calculate deadlines
    total_exec_time = 0
    total_energy = 0
    per_function_deadlines = {}

    for func, options in filtered_data.items():
        for idx, option in enumerate(options):
            if pulp.value(decision_vars[(func, idx)]) == 1:
                chosen_freq = option['frequency']
                exec_time = option['exec_time']
                energy = option['energy']
                deadline_fraction = exec_time
                per_function_deadlines[func] = {
                    'frequency': chosen_freq,
                    'exec_time': exec_time,
                    'energy': energy,
                    'deadline_fraction': deadline_fraction
                }
                total_exec_time += exec_time
                total_energy += energy
                break

    for func, options in filtered_data.items():
        per_function_deadlines[func]['deadline_fraction'] *= slo
        per_function_deadlines[func]['deadline_fraction'] /= total_exec_time

    return {
        'per_function_deadlines': per_function_deadlines,
        'total_execution_time': total_exec_time,
        'total_energy': total_energy
    }

# -------------------------------
# gRPC Server Implementation
# -------------------------------

class WorkflowControllerServicer(workflow_controller_pb2_grpc.WorkflowControllerServicer):
    def __init__(self, profiling_data):
        self.profiling_data = profiling_data

    def OptimizeDeadlines(self, request, context):
        functions = request.functions
        slo = request.slo

        # Validate input
        if not functions:
            return workflow_controller_pb2.OptimizeResponse(
                message="Error: No functions provided in the request."
            )
        if slo <= 0:
            return workflow_controller_pb2.OptimizeResponse(
                message="Error: SLO must be a positive number."
            )

        try:
            # Perform optimization
            result = optimize_deadlines(self.profiling_data, functions, slo)

            # Prepare the response
            deadlines = []
            for func_instance, details in result['per_function_deadlines'].items():
                deadline = workflow_controller_pb2.FunctionDeadline(
                    function_name=func_instance,  # Now includes instance identifier
                    frequency=details['frequency'],
                    exec_time=details['exec_time'],
                    energy=details['energy'],
                    deadline_fraction=details['deadline_fraction']
                )
                deadlines.append(deadline)

            response = workflow_controller_pb2.OptimizeResponse(
                deadlines=deadlines,
                total_execution_time=result['total_execution_time'],
                total_energy=result['total_energy'],
                message="Optimization successful."
            )
            return response

        except ValueError as ve:
            return workflow_controller_pb2.OptimizeResponse(
                message=f"Error: {str(ve)}"
            )
        except Exception as e:
            return workflow_controller_pb2.OptimizeResponse(
                message=f"Error: {str(e)}"
            )

def serve():
    # Load profiling data from CSV
    csv_file = 'profiling.csv'  # Ensure this path is correct
    profiling_data = load_profiling_data(csv_file)

    if not profiling_data:
        print("Failed to load profiling data. Server cannot start.")
        return

    # Create a gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    workflow_controller_pb2_grpc.add_WorkflowControllerServicer_to_server(
        WorkflowControllerServicer(profiling_data), server
    )

    # Listen on port 50051
    server.add_insecure_port('[::]:50051')
    server.start()
    print("WorkflowController gRPC server is running on port 50051.")
    try:
        while True:
            time.sleep(86400)  # One day in seconds
    except KeyboardInterrupt:
        print("Shutting down the server.")
        server.stop(0)

if __name__ == "__main__":
    serve()
