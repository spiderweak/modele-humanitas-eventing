import numpy as np
import gurobipy as gp
from gurobipy import GRB

def O_N_M(env, num_dev, num_comp, num_app, num_resource, pos_app, comp_app, pos_dev, cap_comp_nod, cap_dev_nod, cap_dev_lnk, app_dev_mxd, dim, LAPL):

    prob = gp.Model(env=env.math_env)

    ######################################### Definition of a number of parameters which are used later in the process of O-N-M formulation
    pos_comp=np.array([[0 for col in range(num_comp)] for row in range(dim)], dtype=float)     #Position of all Comps of all Apps in 2D (m)
    c: int=0              #Counter used in iteration
    for i in range(num_app):
        for j in range(comp_app[i]):
            pos_comp[:,c+j]=pos_app[:,i]
        c = c + comp_app[i]


    ZE=np.array([0 for col in range(num_app+1)], dtype=int)   #Same as vector gamma in my formulation
    c: int=0              #Counter used in iteration
    for i in range(num_app):
        c = c + comp_app[i]
        ZE[i+1]=c

    ########################################## Formulating O-N-M
    # Decision Variables: 
    ##########################################
    x = {}
    for u in range(num_comp):
        for i in range(num_dev):
            x[u, i] = prob.addVar(vtype=GRB.BINARY, name="x[%d,%d]" % (u, i), lb=0, ub=1)  #INTEGER

    y = {}
    for s in range(num_app):
        y[s] = prob.addVar(vtype=GRB.BINARY, name="y[%d]" % (s), lb=0, ub=1)  #INTEGER

    # Cost Function:
    ##########################################
    prob.setObjective(gp.quicksum(y[j] for j in range(num_app)), sense=GRB.MAXIMIZE)

    # Constraints og O-N-M:
    ################################################
    for u in range(num_comp):
        prob.addConstr(gp.quicksum(x[u, i] for i in range(num_dev)) <= 1)


    for j in range(num_app):
        prob.addConstr(gp.quicksum(x[u, i] for u in range(ZE[j], ZE[j+1]) for i in range(num_dev)) == y[j]*comp_app[j])


    for i in range(num_dev):
        for u in range(num_comp):
            prob.addConstr(((pos_dev[0][i]-pos_comp[0][u])**2 + (pos_dev[1][i]-pos_comp[1][u])**2)*x[u, i] <= (app_dev_mxd**2))


    for i in range(num_dev):
        for k in range(num_resource):
            prob.addConstr(gp.quicksum(x[u, i]*cap_comp_nod[u][k] for u in range(num_comp)) <= cap_dev_nod[i][k])


    for i in range(num_dev):
        prob.addConstr(gp.quicksum(LAPL[u1][u2]*x[u1, i]*x[u2, i] for u1 in range(num_comp) for u2 in range(num_comp)) <=\
                        gp.quicksum(cap_dev_lnk[i][k] for k in range(num_dev)))

    ################################################
    prob.optimize()
    ################################################
    comp_dev_asg=np.array([[0 for col in range(num_comp)] for row in range(num_dev)], dtype=float)
    for i in range(num_dev):
        for u in range(num_comp):
            if x[u, i].X == 1.0:
                comp_dev_asg[i][u]=1
    ################################################
    np.save("comp_dev_asg.npy", comp_dev_asg)
    np.save("ZE.npy", ZE)
    ################################################
    return comp_dev_asg, ZE