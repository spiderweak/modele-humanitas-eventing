import pulp
import json

class FullStateProcessing:
    """
    Parameters:
        nodes: nodes have multiple resources.
        applications: application have a multi-resource request.

    Constraints:
    - Global Device Resources : The cumulative application deployment cannot exceed to globally available resources
    - Local Device Resources : On each device, the application parts deployed cannot exceed the devices' available resources.
    - Application Integrity : For each application, each process is deployed once and only once on the infrastructure
    - Application Integrity : For each application, either all process are deployed, or none.

    Input:
    Matrix:
        size_1 : num_app*3(=max_num_proc)*4(num_resources) of 1s and 0s.
        size_2 : num_devices

    Output:
    Values : 1s and 0s.
        1 : deploy proc on device
        0 : don't

    Constraints:
    Sum value on a column is 1 : proc deployed there
    sum value on a column is 0 : no proc deployed, error or no proc in this slot for this app
    3-by-3 column sum, 0 (no app deployed) or num_proc (app deployed)
    """


    def __init__(self) -> None:
        pass

class CeilingUnlimitedMigration(FullStateProcessing):

    # Goal of this, handle unlimited migrations, serves as ceiling for deployment informations

    def __init__(self, proc_matrix, dev_matrix) -> None:
        super().__init__()
        self.proc_matrix = proc_matrix
        self.dev_matrix = dev_matrix

    def processing(self):
        # Define the problem
        prob = pulp.LpProblem("MILP_Problem", pulp.LpMaximize)

        # Parameters
        num_proc = 3
        K = 4    # Number of resources

        As = self.proc_matrix

        dict_keys = ['cpu', 'gpu', 'mem', 'disk']
        app_dataset = {'cpu': [], 'gpu': [], 'mem': [], 'disk': []}

        for app in As:
            for key in dict_keys:
                app_dataset[key] += app[key] + [0] * (3 - len(app[key]))
        p_s_u_k = [[[app_dataset[dict_keys[k]][s*num_proc+u] for k in range(K)] for u in range(num_proc)] for s in range(len(As))]

        num_apps = len(As) # Number of applications

        D = self.dev_matrix

        num_devices = len(D['cpu'])

        d_i_k = [[D[dict_keys[k]][i] for k in range(K)] for i in range(num_devices)]

        # Create a dictionary of binary decision variables
        x = pulp.LpVariable.dicts("x", [(s, u, i) for s in range(num_apps) for u in range(num_proc) for i in range(num_devices)], cat="Binary")
        y = pulp.LpVariable.dicts("y", [s for s in range(num_apps)], cat="Binary")

        # Objective function
        prob += pulp.lpSum(y[s] for s in range(num_apps)), "Total number of apps deployed"

        # Application Integrity: each process is deployed once and only once on the infrastructure
        for s in range(num_apps):
            for u in range(num_proc):
                prob += pulp.lpSum(x[(s, u, i)] for i in range(num_devices)) == 1

        # Global and Local Device Resources constraints
        for i in range(num_devices):
            for k in range(K):
                prob += pulp.lpSum(x[(s, u, i)] * p_s_u_k[s][u][k] for s in range(num_apps) for u in range(num_proc)) <= d_i_k[i][k]

        # Application Integrity: all processes of an app are deployed or none are deployed
        for s in range(num_apps):
            for u in range(num_proc):
                prob += pulp.lpSum(x[(s, 0, i)] for i in range(num_devices)) == pulp.lpSum(x[(s, u, i)] for i in range(num_devices))

        # Define the constraints to link y[s] with x[s][u][i]
        for s in range(num_apps):
            for u in range(num_proc):
                prob += pulp.lpSum(x[(s, u, i)] for i in range(num_devices)) >= y[s]

            prob += pulp.lpSum(x[(s, u, i)] for u in range(num_proc) for i in range(num_devices)) <= num_proc * y[s]

        # Solve the problem
        prob.solve()

        for s in range(num_apps):
            for u in range(num_proc):
                for i in range(num_devices):
                    if x[(s,u,i)].value() == 1.0:
                        if sum(p_s_u_k[s][u][k] for k in range(K)) !=0:
                            print(f"Process {u} of Application {s} is deployed on Device {i}")

        return x


class CeilingUnlimitedMigrationWithRetainedState(FullStateProcessing):


    # This tries to deploy/undeploy based on input in batches, with a goal to keep the current state

    # If current state cannot handle deployment, we deploy a batch with deployed+need

    # If batch cannot be deployed, we probably need to represent sum of need against sum of resources
    def __init__(self) -> None:
        super().__init__()


